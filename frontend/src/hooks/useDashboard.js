import { useEffect, useMemo, useState } from 'react'
import { getDashboardSummary } from '../services/dashboardService'
import { getComponents } from '../services/componentService'
import { connectSocket } from '../services/socketService'
import { getStoredUser } from '../utils/storage'
import { MACHINE_KEYS, MACHINE_LABELS } from '../constants/machines'

function createSeedSparkline() {
  const now = Date.now()
  return Array.from({ length: 20 }, (_, idx) => ({
    idx,
    value: Number((20 + Math.sin(idx / 3) * 4 + (idx % 3)).toFixed(2)),
    timestamp: new Date(now - (20 - idx) * 2000).toISOString(),
  }))
}

export default function useDashboard() {
  const user = useMemo(() => getStoredUser(), [])
  const [components, setComponents] = useState([])

  const [summary, setSummary] = useState({
    active_machines: 4,
    open_alerts: 0,
    pending_interventions: 0,
    recent_alerts: [],
    pending_list: [],
  })
  const [machines, setMachines] = useState({})

  const visibleComponents = useMemo(() => {
    const list = components.length
      ? components
      : MACHINE_KEYS.map((machine) => ({ key: machine, name: MACHINE_LABELS[machine], type: machine, enabled: true }))
    if (user?.role === 'technicien' && Array.isArray(user?.machines) && user.machines.length > 0) {
      return list.filter((component) => user.machines.includes(component.type))
    }
    return list
  }, [components, user?.machines, user?.role])

  useEffect(() => {
    let mounted = true
    const loadComponents = async () => {
      try {
        const response = await getComponents()
        if (mounted) {
          const enabled = (response.data.components || []).filter((item) => item.enabled)
          setComponents(enabled)
        }
      } catch {
        if (mounted) {
          setComponents(MACHINE_KEYS.map((machine) => ({ key: machine, name: MACHINE_LABELS[machine], type: machine })))
        }
      }
    }
    loadComponents()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const seed = createSeedSparkline()
    // Reconcile the real-time state when the configured component list changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMachines((prev) => {
      const next = { ...prev }
      visibleComponents.forEach((component) => {
        if (!next[component.key]) {
          next[component.key] = {
            key: component.key,
            type: component.type,
            label: component.name,
            anomalyScore: 20,
            sparkline: [...seed],
          }
        } else {
          next[component.key] = { ...next[component.key], label: component.name, type: component.type }
        }
      })
      return next
    })
  }, [visibleComponents])

  useEffect(() => {
    let isMounted = true

    const fetchSummary = async () => {
      try {
        const { data } = await getDashboardSummary()
        if (isMounted) {
          setSummary((prev) => ({
            ...prev,
            ...data,
            recent_alerts: (data.recent_alerts || []).slice(0, 5),
            pending_list: (data.pending_list || []).slice(0, 5),
          }))
        }
      } catch {
        // Silent fail: dashboard keeps last known values.
      }
    }

    fetchSummary()
    const intervalId = setInterval(fetchSummary, 30000)

    const socket = connectSocket()

    const onAlertNew = (alert) => {
      localStorage.setItem('hasNewAlerts', 'true')
      setSummary((prev) => ({
        ...prev,
        open_alerts: (prev.open_alerts || 0) + 1,
        recent_alerts: [alert, ...(prev.recent_alerts || [])].slice(0, 5),
      }))
    }

    const onSensorData = (prediction) => {
      const machine = prediction?.machine
      const score = Number(prediction?.defect_score ?? prediction?.anomaly_score ?? 0)
      if (!MACHINE_KEYS.includes(machine)) return
      setMachines((prev) => {
        const next = { ...prev }
        let changed = false
        visibleComponents.forEach((component) => {
          if (component.type !== machine) return
          const current = next[component.key]
          if (!current) return
          const nextPoint = {
            idx: Date.now(),
            value: Number((score * 100).toFixed(2)),
            timestamp: prediction?.timestamp || new Date().toISOString(),
          }
          next[component.key] = {
            ...current,
            anomalyScore: Number((score * 100).toFixed(2)),
            sparkline: [...current.sparkline.slice(-19), nextPoint],
          }
          changed = true
        })
        return changed ? next : prev
      })
    }

    socket.on('alert:new', onAlertNew)
    socket.on('sensor:data', onSensorData)

    return () => {
      isMounted = false
      clearInterval(intervalId)
      // Remove only our listeners — do NOT disconnect the singleton socket.
      socket.off('alert:new', onAlertNew)
      socket.off('sensor:data', onSensorData)
    }
  }, [visibleComponents])

  const machineCards = useMemo(
    () => visibleComponents.map((component) => machines[component.key]).filter(Boolean),
    [machines, visibleComponents],
  )

  return {
    summary: {
      ...summary,
      active_machines: visibleComponents.length || summary.active_machines,
    },
    machineCards,
  }
}
