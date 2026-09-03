import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Cell,
  Pie,
  PieChart,
} from 'recharts'
import useDashboard from '../hooks/useDashboard'
import { KPISkeleton, MachineCardSkeleton, AlertListSkeleton } from '../components/SkeletonLoader'
import EmptyState from '../components/EmptyState'
import { 
  FactoryIcon, 
  AlertIcon, 
  ToolIcon, 
  ChartIcon,
  FilterIcon,
  RefreshIcon,
  EyeIcon,
  CalendarIcon,
  UserIcon,
  DownloadIcon,
  ClockIcon
} from '../components/Icons'
import { exportDashboardToPDF } from '../utils/exportPDF'

function getScoreStyle(score) {
  if (score > 70) return { color: '#dc2626', status: 'Critique', badge: 'bg-red-100 text-red-700' }
  if (score >= 40) {
    return { color: '#d97706', status: 'Attention', badge: 'bg-amber-100 text-amber-700' }
  }
  return { color: '#16a34a', status: 'Bon état', badge: 'bg-green-100 text-green-700' }
}

function severityBadge(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700'
  return 'bg-green-100 text-green-700'
}

function timeAgo(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const diff = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000))
  return `il y a ${diff} min`
}

function DashboardPage() {
  const navigate = useNavigate()
  const { summary, machineCards } = useDashboard()
  const [timeFilter, setTimeFilter] = useState('24h')
  const [isLoading, setIsLoading] = useState(false)
  const pendingInterventions = summary.pending_interventions_list || summary.pending_list || []

  const timeFilters = [
    { value: '1h', label: 'Dernière heure' },
    { value: '24h', label: '24 heures' },
    { value: '7d', label: '7 jours' },
    { value: '30d', label: '30 jours' },
  ]

  const handleMachineClick = (machineKey) => {
    navigate(`/surveillance?machine=${machineKey}`)
  }

  const handleAlertClick = (alertId) => {
    navigate(`/alertes/${alertId}`)
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 1000)
    window.location.reload()
  }

  const handleExportPDF = async () => {
    const toastId = toast.loading('Génération du rapport PDF...')
    try {
      const result = await exportDashboardToPDF(summary, machineCards)
      toast.success(`Rapport généré: ${result.fileName}`, { id: toastId, duration: 4000 })
    } catch (error) {
      toast.error(error.message || 'Erreur lors de l\'export PDF', { id: toastId })
    }
  }

  const kpis = [
    { 
      label: 'Machines surveillées', 
      value: summary.active_machines ?? 4,
      icon: FactoryIcon,
      description: 'Équipements actifs',
      color: 'text-blue-600'
    },
    { 
      label: 'Alertes actives', 
      value: summary.open_alerts ?? 0,
      icon: AlertIcon,
      description: 'Nécessitent une attention',
      trend: summary.open_alerts > 0 ? 'warning' : 'success',
      color: 'text-amber-600'
    },
    { 
      label: 'Interventions planifiées', 
      value: summary.pending_interventions ?? 0,
      icon: ToolIcon,
      description: 'Tâches en cours',
      color: 'text-purple-600'
    },
    { 
      label: 'Taux de disponibilité', 
      value: `${Math.max(65, 100 - (summary.open_alerts || 0) * 5).toFixed(0)}%`,
      icon: ChartIcon,
      description: 'Performance globale',
      color: 'text-green-600'
    },
  ]

  // Calculate severity distribution
  const recentAlerts = summary.recent_alerts || []
  const severityStats = recentAlerts.reduce((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1
    return acc
  }, {})

  const severityData = [
    { name: 'Critique', value: severityStats['Critique'] || 0, color: '#dc2626' },
    { name: 'Majeure', value: severityStats['Majeure'] || 0, color: '#d97706' },
    { name: 'Mineure', value: severityStats['Mineure'] || 0, color: '#16a34a' },
  ].filter(item => item.value > 0)

  return (
    <section className="space-y-6">
      {/* Header avec filtres et actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white rounded-xl border border-slate-200 p-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tableau de bord</h1>
          <p className="text-sm text-slate-500 mt-1">Vue d'ensemble en temps réel</p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Filtre temporel */}
          <div className="flex items-center gap-2 bg-slate-50 rounded-lg p-1">
            <FilterIcon className="w-4 h-4 text-slate-400 ml-2" />
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="bg-transparent border-none text-sm font-medium text-slate-700 focus:outline-none pr-2"
            >
              {timeFilters.map(filter => (
                <option key={filter.value} value={filter.value}>
                  {filter.label}
                </option>
              ))}
            </select>
          </div>

          {/* Bouton export PDF */}
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <DownloadIcon className="w-4 h-4" />
            <span className="text-sm font-medium">Export PDF</span>
          </button>

          {/* Bouton refresh */}
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">Actualiser</span>
          </button>
        </div>
      </div>

      {/* KPIs avec icônes SVG */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((metric) => {
          const IconComponent = metric.icon
          return (
            <article key={metric.label} className="rounded-xl border border-slate-200 bg-white p-5 hover:shadow-lg transition-all duration-200 cursor-pointer group">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-slate-500">{metric.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">{metric.value}</p>
                  <p className="mt-1 text-xs text-slate-400">{metric.description}</p>
                </div>
                <div className={`p-3 rounded-lg bg-slate-50 group-hover:scale-110 transition-transform ${metric.color}`}>
                  <IconComponent className="w-6 h-6" />
                </div>
              </div>
              {metric.trend && (
                <div className={`mt-3 text-xs font-medium flex items-center gap-1 ${metric.trend === 'warning' ? 'text-amber-600' : 'text-green-600'}`}>
                  {metric.trend === 'warning' ? (
                    <>
                      <AlertIcon className="w-3 h-3" />
                      <span>Action requise</span>
                    </>
                  ) : (
                    <>
                      <span className="text-green-500">✓</span>
                      <span>Situation normale</span>
                    </>
                  )}
                </div>
              )}
            </article>
          )
        })}
      </div>

      {/* Distribution des alertes par sévérité */}
      {severityData.length > 0 && (
        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Répartition des alertes par criticité</h3>
          <div className="flex items-center justify-center gap-8">
            <div className="h-40 w-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {severityData.map((item) => (
                <div key={item.name} className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: item.color }}></div>
                  <span className="text-sm text-slate-700">{item.name}: <strong>{item.value}</strong></span>
                </div>
              ))}
            </div>
          </div>
        </article>
      )}

      {/* Machines - État en temps réel avec drill-down */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900">État des équipements en temps réel</h2>
          <button
            onClick={() => navigate('/surveillance')}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            <EyeIcon className="w-4 h-4" />
            Voir surveillance détaillée
          </button>
        </div>

        {machineCards.length === 0 ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <MachineCardSkeleton />
            <MachineCardSkeleton />
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {machineCards.map((machine) => {
              const style = getScoreStyle(machine.anomalyScore)
              return (
                <article
                  key={machine.key}
                  onClick={() => handleMachineClick(machine.key)}
                  className="rounded-xl border border-slate-200 bg-white p-5 space-y-4 hover:shadow-lg hover:border-blue-300 transition-all duration-200 cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {machine.label}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${style.badge}`}>
                        {style.status}
                      </span>
                      <EyeIcon className="w-5 h-5 text-slate-400 group-hover:text-blue-600 transition-colors" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 items-center">
                    <div className="h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadialBarChart
                          cx="50%"
                          cy="50%"
                          innerRadius="65%"
                          outerRadius="100%"
                          barSize={14}
                          data={[{ value: machine.anomalyScore }]}
                          startAngle={90}
                          endAngle={-270}
                        >
                          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                          <RadialBar dataKey="value" fill={style.color} cornerRadius={8} />
                        </RadialBarChart>
                      </ResponsiveContainer>
                    </div>

                    <div>
                      <p className="text-sm text-slate-500">Probabilité d'anomalie</p>
                      <p className="text-3xl font-bold" style={{ color: style.color }}>
                        {machine.anomalyScore.toFixed(1)}%
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {machine.anomalyScore < 40 ? 'Fonctionnement normal' : 
                         machine.anomalyScore < 70 ? 'Surveillance accrue' : 
                         'Intervention urgente'}
                      </p>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-slate-500 mb-2">Évolution sur 40 secondes</p>
                    <div className="h-16">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={machine.sparkline}>
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={style.color}
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Cliquez pour voir les détails</span>
                    <span className="text-blue-600 font-medium group-hover:underline">
                      Surveillance →
                    </span>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </div>

      {/* Alertes et Interventions avec drill-down */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <AlertIcon className="w-5 h-5 text-amber-600" />
              Alertes récentes
            </h3>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">Dernières 5</span>
              <button
                onClick={() => navigate('/alertes')}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Voir tout →
              </button>
            </div>
          </div>

          {!summary.recent_alerts ? (
            <AlertListSkeleton count={3} />
          ) : summary.recent_alerts.length === 0 ? (
            <EmptyState
              icon="✅"
              title="Aucune alerte récente"
              description="Tous les équipements fonctionnent normalement"
            />
          ) : (
            <div className="space-y-3">
              {summary.recent_alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => handleAlertClick(alert.id)}
                  className="flex flex-col gap-2 rounded-lg border border-slate-100 p-3 sm:flex-row sm:items-center sm:justify-between hover:bg-blue-50 hover:border-blue-200 transition-all cursor-pointer group"
                >
                  <div className="flex-1">
                    <p className="font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                      {alert.machine}
                    </p>
                    <p className="text-sm text-slate-600 mt-1">
                      <span className="font-medium">Défaut:</span> {alert.defect}
                    </p>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                      <span>Score: {(alert.anomaly_score * 100).toFixed(1)}%</span>
                      <span>•</span>
                      <span>Confiance: {(alert.confidence * 100).toFixed(0)}%</span>
                    </p>
                  </div>
                  <div className="text-right space-y-1 flex-shrink-0">
                    <span
                      className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${severityBadge(alert.severity)}`}
                    >
                      {alert.severity}
                    </span>
                    <p className="text-xs text-slate-400 flex items-center gap-1 justify-end">
                      <ClockIcon className="w-3 h-3" />
                      {timeAgo(alert.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <ToolIcon className="w-5 h-5 text-purple-600" />
              Interventions à planifier
            </h3>
            <span className="text-xs bg-slate-100 px-2 py-1 rounded-full font-medium text-slate-700">
              {pendingInterventions.length} tâche(s)
            </span>
          </div>

          {pendingInterventions.length === 0 ? (
            <EmptyState
              icon="✅"
              title="Aucune intervention en attente"
              description="Toutes les alertes ont été traitées"
            />
          ) : (
            <div className="space-y-3">
              {pendingInterventions.slice(0, 5).map((item) => (
                <div 
                  key={item.id} 
                  onClick={() => handleAlertClick(item.id)}
                  className="rounded-lg border border-slate-100 p-3 hover:bg-purple-50 hover:border-purple-200 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-slate-900 group-hover:text-purple-600 transition-colors">
                        {item.machine}
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        <span className="font-medium">Défaut:</span> {item.defect || 'Non spécifié'}
                      </p>
                    </div>
                    <span className={`rounded-full px-2 py-1 text-xs font-semibold flex-shrink-0 ${severityBadge(item.severity)}`}>
                      {item.severity}
                    </span>
                  </div>
                  <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-500 flex items-center gap-1">
                      <UserIcon className="w-3 h-3" />
                      {item.assigned_to_name || `Technicien #${item.assigned_to}` || 'Non assigné'}
                    </span>
                    <span className="text-slate-400 flex items-center gap-1">
                      <CalendarIcon className="w-3 h-3" />
                      {item.deadline
                        ? new Date(item.deadline).toLocaleDateString('fr-FR')
                        : item.resolved_at
                          ? new Date(item.resolved_at).toLocaleDateString('fr-FR')
                          : 'À planifier'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </div>
    </section>
  )
}

export default DashboardPage
