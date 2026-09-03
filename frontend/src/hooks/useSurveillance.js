import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import api from '../services/api'
import { connectSocket } from '../services/socketService'
import { getStoredUser } from '../utils/storage'

const SIMULATION_ENABLED =
  import.meta.env.VITE_ENABLE_SIMULATION === 'true' || import.meta.env.DEV

const MACHINES = {
  moteur: 'Moteur',
  pompe: 'Pompe',
  compresseur: 'Compresseur',
  echangeur: 'Échangeur',
}

// V7 sensor names (matching backend V7 models)
const MACHINE_SENSORS = {
  moteur: ['vbl_feature_00', 'vbl_feature_01', 'vbl_feature_02'],  // V7: Pre-computed VBL features
  pompe: ['vibration', 'pressure', 'temperature', 'flow_rate'],    // V7: 4 sensors
  compresseur: ['pressure', 'temperature_oil', 'current'],         // V7: 3 sensors
  echangeur: ['temp_in_hot', 'temp_out_hot', 'temp_in_cold', 'temp_out_cold', 'flow_rate'],  // V7: 5 sensors
}

const DEFECT_OPTIONS_BY_TYPE = {
  moteur: ['degradation_roulement', 'desequilibre_desalignement'],
  pompe: ['cavitation', 'usure_garniture_mecanique'],
  compresseur: ['usure_soupapes', 'refroidissement_huile'],
  echangeur: ['encrassement_progressif', 'fuite_interne'],
}

const CHART_BUFFER_MAX = 60

function toLabel(name) {
  return name.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function normalizeMachine(machine) {
  return String(machine || '').trim().toLowerCase()
}

// Build a default sensor list with zero values for a given machine type
function defaultSensorList(machineType) {
  return (MACHINE_SENSORS[machineType] || []).map((sensor) => ({
    name: sensor,
    label: toLabel(sensor),
    value: 0,
  }))
}

export default function useSurveillance() {
  const user = useMemo(() => getStoredUser(), [])
  const [components, setComponents] = useState([])
  const [activeMachine, setActiveMachine] = useState('moteur')
  const [anomalyScore, setAnomalyScore] = useState(0)
  const [defectScores, setDefectScores] = useState({})
  const [modelName, setModelName] = useState('')
  const [requiredSensors, setRequiredSensors] = useState([])
  const [sensorList, setSensorList] = useState([])
  const [lastDefect, setLastDefect] = useState(null)
  const [defectHistory, setDefectHistory] = useState([])
  const [simulationMode, setSimulationMode] = useState(false)
  const [liveDataUnavailable, setLiveDataUnavailable] = useState(false)
  // chartData drives the charts — updated by the 1-second ticker below.
  const [chartData, setChartData] = useState([])

  // Per-machine rolling buffers stored in a ref so writes don't trigger renders.
  const chartBuffersRef = useRef({})
  const lastLiveMessageAtRef = useRef(0)

  const getChartBuffer = useCallback((machineKey) => {
    if (!chartBuffersRef.current[machineKey]) {
      chartBuffersRef.current[machineKey] = []
    }
    return chartBuffersRef.current[machineKey]
  }, [])

  // ── Derived state ──────────────────────────────────────────────────────────

  const tabs = useMemo(() => {
    if (components.length > 0) {
      return components.map((component) => ({
        key: component.key,
        label: component.name,
        type: component.type,
      }))
    }
    return Object.entries(MACHINES).map(([key, label]) => ({ key, label, type: key }))
  }, [components])

  const activeTab = useMemo(
    () => tabs.find((tab) => tab.key === activeMachine) || tabs[0] || null,
    [activeMachine, tabs],
  )

  const activeType = activeTab?.type || activeMachine

  // Keep activeMachine in sync when tabs change
  useEffect(() => {
    if (tabs.length > 0 && !tabs.some((tab) => tab.key === activeMachine)) {
      setActiveMachine(tabs[0].key)
    }
  }, [activeMachine, tabs])

  // ── Load components from API ───────────────────────────────────────────────

  useEffect(() => {
    let mounted = true

    const loadComponents = async () => {
      try {
        const response = await api.get('/api/components')
        const allComponents = (response.data.components || []).filter((item) => item.enabled)
        const visibleComponents =
          user?.role === 'technicien' && Array.isArray(user?.machines) && user.machines.length > 0
            ? allComponents.filter((component) => user.machines.includes(component.type))
            : allComponents
        if (mounted) {
          setComponents(visibleComponents)
          if (visibleComponents.length > 0) {
            setActiveMachine((prev) =>
              visibleComponents.some((component) => component.key === prev)
                ? prev
                : visibleComponents[0].key,
            )
          }
        }
      } catch {
        if (mounted) {
          const fallback = Object.entries(MACHINES).map(([key, label]) => ({
            key,
            name: label,
            type: key,
          }))
          setComponents(fallback)
          setActiveMachine((prev) =>
            fallback.some((item) => item.key === prev) ? prev : fallback[0].key,
          )
        }
      }
    }

    loadComponents()
    return () => {
      mounted = false
    }
  }, [user?.machines, user?.role])

  // ── Reset state when active machine changes ────────────────────────────────

  useEffect(() => {
    setChartData([...getChartBuffer(activeMachine)])
    setAnomalyScore(0)
    setSensorList(defaultSensorList(activeType))
    setLastDefect(null)
    setDefectHistory([])
    setDefectScores({})
    setModelName('')
    setRequiredSensors([])
    setSimulationMode(false)
    setLiveDataUnavailable(false)
    lastLiveMessageAtRef.current = 0
  }, [activeMachine, activeType, getChartBuffer])

  // ── Process an incoming payload (live or simulated) ────────────────────────

  // Wrapped in useCallback with no deps so it can be used inside effects
  // without triggering unnecessary re-subscriptions.
  const activeTypeRef = useRef(activeType)
  const activeMachineRef = useRef(activeMachine)
  useEffect(() => { activeTypeRef.current = activeType }, [activeType])
  useEffect(() => { activeMachineRef.current = activeMachine }, [activeMachine])

  const applyPayload = useCallback((payload) => {
    if (!payload) return
    const payloadMachine = normalizeMachine(payload.machine)
    if (payloadMachine !== normalizeMachine(activeTypeRef.current)) return

    lastLiveMessageAtRef.current = Date.now()
    setSimulationMode(false)
    setLiveDataUnavailable(false)

    const sensors = payload.sensors || {}
    const timestampRaw = payload.timestamp || new Date().toISOString()
    const chartPoint = {
      timestamp: new Date(timestampRaw).toLocaleTimeString('fr-FR', { hour12: false }),
      ...sensors,
    }

    // Update buffer immediately; chartData state is flushed by the ticker below.
    const key = activeMachineRef.current
    const prev = getChartBuffer(key)
    chartBuffersRef.current[key] = [...prev, chartPoint].slice(-CHART_BUFFER_MAX)

    const score = Number(payload.defect_score ?? payload.anomaly_score ?? 0)
    const liveDefectScores =
      payload.defect_scores && typeof payload.defect_scores === 'object'
        ? payload.defect_scores
        : {}

    setAnomalyScore(Math.round(score * 100))
    setDefectScores(liveDefectScores)
    setModelName(payload.model_name || '')
    setRequiredSensors(Array.isArray(payload.required_sensors) ? payload.required_sensors : [])

    const sensorItems = Object.entries(sensors)
      .filter(([name]) => !name.endsWith('_max') && !name.endsWith('_min') &&
        !name.endsWith('_mean') && !name.endsWith('_sd') && !name.endsWith('_rms') &&
        !name.endsWith('_skewness') && !name.endsWith('_kurtosis') &&
        !name.endsWith('_crest') && !name.endsWith('_form'))
      .map(([name, value]) => ({
        name,
        label: toLabel(name),
        value: typeof value === 'number' ? value : Number(value || 0),
      }))

    if (sensorItems.length > 0) {
      setSensorList(sensorItems)
    }

    if (payload.defect && payload.defect !== 'normal_operation') {
      const defectItem = {
        timestamp: timestampRaw,
        defect: payload.defect,
        defectScores: liveDefectScores,
        confidence: Math.round((payload.confidence || 0) * 100),
        modelName: payload.model_name || '',
        requiredSensors: Array.isArray(payload.required_sensors) ? payload.required_sensors : [],
        status: score >= 0.85 ? 'Critique' : 'Surveillance',
      }
      setLastDefect(defectItem)
      setDefectHistory((h) => [defectItem, ...h].slice(0, 30))
    }
  }, [getChartBuffer])

  // ── Socket subscription ────────────────────────────────────────────────────

  useEffect(() => {
    const socket = connectSocket()

    const onConnect = () => setLiveDataUnavailable(false)
    const onConnectError = () => setLiveDataUnavailable(true)
    const onDisconnect = () => setLiveDataUnavailable(true)
    const onSensorData = (data) => applyPayload(data)

    socket.on('connect', onConnect)
    socket.on('connect_error', onConnectError)
    socket.on('disconnect', onDisconnect)
    socket.on('sensor:data', onSensorData)

    // Ticker: flush the buffer ref into React state so charts re-render
    const chartTicker = setInterval(() => {
      setChartData([...getChartBuffer(activeMachineRef.current)])
    }, 1000)

    // Simulation / liveness check ticker
    const simulationTicker = setInterval(() => {
      const lastLiveAge = Date.now() - lastLiveMessageAtRef.current
      const hasReceivedLiveData = lastLiveMessageAtRef.current > 0

      if (!SIMULATION_ENABLED) {
        setSimulationMode(false)
        setLiveDataUnavailable(hasReceivedLiveData && lastLiveAge >= 3500)
        return
      }

      if (lastLiveAge < 3500) {
        setLiveDataUnavailable(false)
        return
      }

      setSimulationMode(true)
      setLiveDataUnavailable(false)

      const currentType = activeTypeRef.current
      const sensors = {}

      for (const sensor of MACHINE_SENSORS[currentType] || []) {
        if (sensor.includes('temp')) {
          sensors[sensor] = Number((40 + Math.random() * 45).toFixed(2))
        } else if (sensor.includes('pressure')) {
          sensors[sensor] = Number((3 + Math.random() * 8).toFixed(2))
        } else if (sensor.includes('flow')) {
          sensors[sensor] = Number((80 + Math.random() * 80).toFixed(2))
        } else if (sensor.includes('current')) {
          sensors[sensor] = Number((8 + Math.random() * 14).toFixed(2))
        } else {
          sensors[sensor] = Number((0.15 + Math.random() * 1.6).toFixed(3))
        }
      }

      const anomaly = Math.min(
        0.98,
        Math.max(
          0.05,
          Object.values(sensors).reduce((sum, value) => sum + Number(value), 0) /
            (Object.keys(sensors).length * 100),
        ),
      )
      const defects = DEFECT_OPTIONS_BY_TYPE[currentType] || ['defaut_1', 'defaut_2']
      const firstScore = Number(Math.max(0, anomaly - 0.12).toFixed(4))
      const secondScore = Number(Math.min(0.99, anomaly + 0.09).toFixed(4))
      const simulatedDefectScores = {
        [defects[0]]: firstScore,
        [defects[1]]: secondScore,
      }
      const topDefect = firstScore >= secondScore ? defects[0] : defects[1]

      applyPayload({
        machine: currentType,
        sensors,
        defect_score: anomaly,
        anomaly_score: anomaly,
        defect_scores: simulatedDefectScores,
        confidence: 0.65 + Math.random() * 0.3,
        defect: anomaly > 0.45 ? topDefect : 'normal_operation',
        timestamp: new Date().toISOString(),
      })
    }, 2000)

    return () => {
      clearInterval(chartTicker)
      clearInterval(simulationTicker)
      // Remove only our listeners — do NOT disconnect the singleton socket.
      socket.off('connect', onConnect)
      socket.off('connect_error', onConnectError)
      socket.off('disconnect', onDisconnect)
      socket.off('sensor:data', onSensorData)
    }
    // applyPayload and getChartBuffer are stable callbacks; re-run only when
    // the component mounts/unmounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Derived chart series ───────────────────────────────────────────────────

  const chartSeriesBySensor = useMemo(() => {
    const series = {}
    for (const sensor of sensorList) {
      series[sensor.name] = chartData.map((point) => ({
        timestamp: point.timestamp,
        value:
          typeof point[sensor.name] === 'number'
            ? point[sensor.name]
            : Number(point[sensor.name] ?? 0),
      }))
    }
    return series
  }, [chartData, sensorList])

  return {
    tabs,
    activeMachine,
    setActiveMachine,
    chartData,
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
  }
}
