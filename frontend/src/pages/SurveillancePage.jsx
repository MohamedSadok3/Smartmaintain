import { useState } from 'react'
import {
  Line,
  LineChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Bar,
  BarChart,
  Cell,
} from 'recharts'
import useSurveillance from '../hooks/useSurveillance'
import LoadingSpinner from '../components/LoadingSpinner'
import { formatDateTime, formatChartTime, extractHour } from '../utils/dateUtils'
import EmptyState from '../components/EmptyState'
import { 
  AlertIcon, 
  ChartIcon, 
  ToolIcon,
  TrendUpIcon,
  TrendDownIcon,
  FilterIcon,
  DownloadIcon,
  EyeIcon
} from '../components/Icons'

const SENSOR_COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2']

const SENSOR_UNITS = {
  vibration: 'g',
  current: 'A',
  temperature: '°C',
  pressure_in: 'bar',
  pressure_out: 'bar',
  flow_rate: 'm3/h',
  pressure: 'bar',
  temperature_oil: '°C',
  temperature_air: '°C',
  temp_in_hot: '°C',
  temp_out_hot: '°C',
  temp_in_cold: '°C',
  temp_out_cold: '°C',
}

function getScoreColor(score) {
  if (score > 70) return '#dc2626'
  if (score >= 40) return '#f59e0b'
  return '#16a34a'
}

function sensorDotColor(value) {
  if (value > 80) return 'bg-red-500'
  if (value > 50) return 'bg-amber-500'
  return 'bg-green-500'
}

// formatTime is now imported from utils/dateUtils.js as formatDateTime

function humanize(value) {
  return (value || '').replaceAll('_', ' ')
}

const CHART_HEIGHT = 240

function SensorChart({ sensor, seriesData, color, showTrend = true }) {
  const unit = SENSOR_UNITS[sensor.name] || ''
  
  // Calculer la tendance
  let trend = null
  if (showTrend && seriesData.length >= 2) {
    const recent = seriesData.slice(-5)
    const firstVal = recent[0]?.value || 0
    const lastVal = recent[recent.length - 1]?.value || 0
    const change = ((lastVal - firstVal) / (firstVal || 1)) * 100
    trend = {
      direction: change > 0 ? 'up' : 'down',
      percentage: Math.abs(change).toFixed(1)
    }
  }

  // Détecter les valeurs anormales
  const values = seriesData.map(d => d.value)
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  const threshold = avg * 1.5

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 hover:shadow-md transition-shadow">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-slate-800">{sensor.label}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-900">
              {Number(sensor.value).toFixed(2)}
            </span>
            <span className="text-xs text-slate-500">{unit}</span>
          </div>
        </div>
        {trend && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${
            trend.direction === 'up' ? 'bg-amber-50 text-amber-700' : 'bg-green-50 text-green-700'
          }`}>
            {trend.direction === 'up' ? (
              <TrendUpIcon className="w-3 h-3" />
            ) : (
              <TrendDownIcon className="w-3 h-3" />
            )}
            <span className="text-xs font-medium">{trend.percentage}%</span>
          </div>
        )}
      </div>
      <div style={{ width: '100%', height: CHART_HEIGHT }}>
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <AreaChart data={seriesData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`gradient-${sensor.name}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={color} stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis 
              dataKey="timestamp" 
              tick={{ fontSize: 10, fill: '#64748b' }} 
              interval="preserveStartEnd"
              stroke="#cbd5e1"
            />
            <YAxis 
              tick={{ fontSize: 10, fill: '#64748b' }} 
              width={48}
              stroke="#cbd5e1"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              formatter={(value) => [`${Number(value).toFixed(2)}${unit ? ` ${unit}` : ''}`, sensor.label]}
              labelFormatter={(label) => `Heure : ${label}`}
            />
            <Area
              dataKey="value"
              name={sensor.label}
              type="monotone"
              stroke={color}
              strokeWidth={2}
              fill={`url(#gradient-${sensor.name})`}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </article>
  )
}

function SurveillancePage() {
  const {
    tabs,
    activeMachine,
    setActiveMachine,
    chartSeriesBySensor,
    anomalyScore,
    defectScores,
    modelName,
    requiredSensors,
    sensorList,
    defectHistory,
    lastDefect,
    simulationMode,
    liveDataUnavailable,
  } = useSurveillance()

  const [timeRange, setTimeRange] = useState('24h')
  const [viewMode, setViewMode] = useState('grid') // Ajout de viewMode manquant

  const scoreColor = getScoreColor(anomalyScore)
  const gaugeData = [{ name: 'score', value: anomalyScore, fill: scoreColor }]
  const hasTabs = tabs.length > 0
  const defectScoreEntries = Object.entries(defectScores || {})

  // Préparer les données pour la heatmap des alertes (24h divisées en heures)
  const alertHeatmapData = Array.from({ length: 24 }, (_, hour) => {
    const hourDefects = defectHistory.filter(d => {
      const defectHour = extractHour(d.timestamp)
      return defectHour === hour
    })
    return {
      hour: `${hour}h`,
      count: hourDefects.length,
      severity: hourDefects.length > 5 ? 'high' : hourDefects.length > 2 ? 'medium' : 'low'
    }
  })

  const getHeatmapColor = (count) => {
    if (count === 0) return '#f1f5f9' // slate-100
    if (count <= 2) return '#bfdbfe' // blue-200
    if (count <= 5) return '#fbbf24' // amber-400
    return '#dc2626' // red-600
  }

  return (
    <section className="space-y-6">
      {/* Header avec navigation et contrôles */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <EyeIcon className="w-6 h-6 text-blue-600" />
              Surveillance en temps réel
            </h1>
            <p className="text-sm text-slate-500 mt-1">Analyse des capteurs et détection d'anomalies</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Sélecteur de période */}
            <div className="flex items-center gap-2 bg-slate-50 rounded-lg p-1">
              <FilterIcon className="w-4 h-4 text-slate-400 ml-2" />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="bg-transparent border-none text-sm font-medium text-slate-700 focus:outline-none pr-2"
              >
                <option value="1h">Dernière heure</option>
                <option value="24h">24 heures</option>
                <option value="7d">7 jours</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Onglets de machines */}
      <div className="flex flex-wrap gap-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveMachine(tab.key)}
            className={`rounded-xl px-5 py-3 text-sm font-medium transition-all ${
              activeMachine === tab.key
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-blue-300'
            }`}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {!hasTabs && (
        <EmptyState
          icon="🏭"
          title="Aucun équipement disponible"
          description="Aucun composant actif pour ce profil utilisateur"
        />
      )}
      {/* Alertes de statut */}
      {simulationMode && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 flex items-start gap-3">
          <AlertIcon className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-900">Mode développement</p>
            <p className="text-xs text-amber-700 mt-1">
              Mesures simulées pour {tabs.find((t) => t.key === activeMachine)?.label}            </p>
          </div>
        </div>
      )}
      
      {liveDataUnavailable && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 flex items-start gap-3">
          <AlertIcon className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-900">Flux capteurs indisponible</p>
            <p className="text-xs text-red-700 mt-1">
              Les données affichées peuvent être obsolètes
            </p>
          </div>
        </div>
      )}

      {hasTabs && (
        <div className="grid grid-cols-1 xl:grid-cols-10 gap-6">
          {/* Colonne principale - Graphiques */}
          <div className="xl:col-span-7 space-y-6">
            {/* Section capteurs */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <ChartIcon className="w-5 h-5 text-blue-600" />
                  Capteurs en temps réel
                </h2>
                <span className="text-sm text-slate-500">{sensorList.length} capteur(s) actif(s)</span>
              </div>
              
              {sensorList.length === 0 ? (
                <EmptyState
                  icon="📊"
                  title="Aucune mesure disponible"
                  description="Aucun capteur actif pour cette machine"
                />
              ) : (
                <div className={`grid gap-4 ${
                  viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'
                }`}>
                  {sensorList.map((sensor, index) => (
                    <SensorChart
                      key={`${activeMachine}-${sensor.name}`}
                      sensor={sensor}
                      seriesData={chartSeriesBySensor[sensor.name] || []}
                      color={SENSOR_COLORS[index % SENSOR_COLORS.length]}
                      showTrend={true}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Heatmap des alertes sur 24h */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <AlertIcon className="w-5 h-5 text-amber-600" />
                Carte thermique des alertes (24h)
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={alertHeatmapData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis 
                      dataKey="hour" 
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      stroke="#cbd5e1"
                    />
                    <YAxis 
                      label={{ value: 'Nombre d\'alertes', angle: -90, position: 'insideLeft', fontSize: 11 }}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      stroke="#cbd5e1"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        fontSize: '12px'
                      }}
                      formatter={(value) => [`${value} alerte(s)`, 'Nombre']}
                    />
                    <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                      {alertHeatmapData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getHeatmapColor(entry.count)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center justify-center gap-6 mt-4 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f1f5f9' }} />
                  <span className="text-slate-600">Aucune</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#bfdbfe' }} />
                  <span className="text-slate-600">Faible (1-2)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#fbbf24' }} />
                  <span className="text-slate-600">Moyen (3-5)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#dc2626' }} />
                  <span className="text-slate-600">Élevé (6+)</span>
                </div>
              </div>
            </article>

            {/* Historique des défauts */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <ToolIcon className="w-5 h-5 text-purple-600" />
                Historique des défauts
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-slate-600 border-b-2 border-slate-200 font-medium">
                      <th className="py-3 px-2">Horodatage</th>
                      <th className="py-3 px-2">Défaut</th>
                      <th className="py-3 px-2">Confiance</th>
                      <th className="py-3 px-2">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {defectHistory.slice(0, 10).map((item, idx) => (
                      <tr 
                        key={`${item.timestamp}-${idx}`} 
                        className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                      >
                        <td className="py-3 px-2 text-slate-700">{formatDateTime(item.timestamp)}</td>
                        <td className="py-3 px-2 font-medium text-slate-900">{humanize(item.defect)}</td>
                        <td className="py-3 px-2">
                          <span className="text-slate-700">{item.confidence}%</span>
                        </td>
                        <td className="py-3 px-2">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            item.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                          }`}>
                            {item.status === 'resolved' ? '✓ Résolu' : '⏳ En attente'}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {defectHistory.length === 0 && (
                      <tr>
                        <td className="py-8 text-center text-slate-500" colSpan={4}>
                          <EmptyState
                            icon="✅"
                            title="Aucun défaut détecté"
                            description="Tous les systèmes fonctionnent normalement"
                          />
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </article>
          </div>

          {/* Colonne latérale - Stats et scores */}
          <div className="xl:col-span-3 space-y-6">
            {/* Score d'anomalie principal */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-slate-900 mb-2">Score d'anomalie</h3>
              <p className="text-xs text-slate-500 mb-4">
                Modèle IA : <span className="font-medium text-slate-700">{modelName || 'N/A'}</span>
              </p>
              <div className="h-56 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    innerRadius="60%"
                    outerRadius="100%"
                    data={gaugeData}
                    startAngle={180}
                    endAngle={0}
                  >
                    <RadialBar 
                      background 
                      dataKey="value" 
                      cornerRadius={10}
                      fill={scoreColor}
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <p className="text-4xl font-bold" style={{ color: scoreColor }}>
                    {anomalyScore}%
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {anomalyScore > 70 ? 'Critique' : anomalyScore >= 40 ? 'Attention' : 'Normal'}
                  </p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">État</span>
                  <span className={`font-medium ${
                    anomalyScore > 70 ? 'text-red-600' : anomalyScore >= 40 ? 'text-amber-600' : 'text-green-600'
                  }`}>
                    {anomalyScore > 70 ? '⚠️ Intervention requise' : anomalyScore >= 40 ? '👁️ Surveillance accrue' : '✅ Fonctionnement normal'}
                  </span>
                </div>
              </div>
            </article>

            {/* Valeurs actuelles des capteurs */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-slate-900 mb-4">Valeurs actuelles</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {sensorList.map((sensor) => {
                  const value = Number(sensor.value)
                  const dotColor = value > 80 ? 'bg-red-500' : value > 50 ? 'bg-amber-500' : 'bg-green-500'
                  
                  return (
                    <div key={sensor.name} className="flex items-center justify-between text-sm group hover:bg-slate-50 p-2 rounded-lg transition-colors">
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${dotColor} group-hover:scale-125 transition-transform`} />
                        <span className="text-slate-700">{sensor.label}</span>
                      </div>
                      <span className="font-semibold text-slate-900">
                        {value.toFixed(2)} <span className="text-xs text-slate-500">{SENSOR_UNITS[sensor.name] || ''}</span>
                      </span>
                    </div>
                  )
                })}
              </div>
            </article>

            {/* Scores des défauts */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-slate-900 mb-4">Probabilités de défauts</h3>
              <div className="space-y-3">
                {defectScoreEntries.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">Aucun score disponible</p>
                ) : (
                  defectScoreEntries.map(([defect, score]) => {
                    const percentage = (Number(score) * 100).toFixed(1)
                    const width = `${percentage}%`
                    const color = Number(score) > 0.7 ? 'bg-red-500' : Number(score) > 0.4 ? 'bg-amber-500' : 'bg-green-500'
                    
                    return (
                      <div key={defect} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-slate-800">{humanize(defect)}</span>
                          <span className="text-slate-900 font-semibold">{percentage}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div 
                            className={`h-full ${color} transition-all duration-500 rounded-full`}
                            style={{ width }}
                          />
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </article>

            {/* Dernier défaut détecté */}
            <article className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="text-base font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <AlertIcon className="w-4 h-4 text-red-600" />
                Dernier défaut détecté
              </h3>
              {lastDefect ? (
                <div className="space-y-3">
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="font-semibold text-slate-900 text-sm mb-2">{humanize(lastDefect.defect)}</p>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Confiance</span>
                        <span className="font-medium text-slate-700">{lastDefect.confidence}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">Modèle</span>
                        <span className="font-medium text-slate-700">{lastDefect.modelName || modelName || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-xs font-medium text-slate-600 mb-2">Capteurs impliqués:</p>
                    <div className="flex flex-wrap gap-1">
                      {(lastDefect.requiredSensors || requiredSensors).slice(0, 6).map((sensor, idx) => (
                        <span 
                          key={idx}
                          className="inline-flex items-center px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium"
                        >
                          {humanize(sensor)}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100">
                    <p className="text-xs text-slate-400">{formatDateTime(lastDefect.timestamp)}</p>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon="✅"
                  title="Aucun défaut récent"
                  description="Système opérationnel"
                />
              )}
            </article>
          </div>
        </div>
      )}
    </section>
  )
}

export default SurveillancePage
