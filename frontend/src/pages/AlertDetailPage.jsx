import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getAlerteById } from '../services/alerteService'
import { UserIcon, CheckCircleIcon, XCircleIcon, ClockIcon, AlertIcon, ChartIcon } from '../components/Icons'
import LoadingSpinner from '../components/LoadingSpinner'

function severityStyles(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700 border-red-200'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700 border-amber-200'
  return 'bg-green-100 text-green-700 border-green-200'
}

function statusStyles(status) {
  if (status === 'resolved') return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  if (status === 'acknowledged') return 'bg-blue-100 text-blue-700 border-blue-200'
  if (status === 'assigned') return 'bg-indigo-100 text-indigo-700 border-indigo-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('fr-FR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function InfoRow({ label, value, emphasis = false, icon }) {
  return (
    <div className={`rounded-xl border px-4 py-3 transition-all ${emphasis ? 'bg-white border-slate-300' : 'bg-slate-50 border-slate-200'}`}>
      <div className="flex items-center gap-2">
        {icon && <span className="text-slate-400">{icon}</span>}
        <p className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">{label}</p>
      </div>
      <p className="mt-1 text-sm font-semibold text-slate-800">{value || '-'}</p>
    </div>
  )
}

function AssignModal({ isOpen, onClose, onAssign, currentAssignee }) {
  const [technicians, setTechnicians] = useState([])
  const [selectedTech, setSelectedTech] = useState(currentAssignee || '')
  const [loading, setLoading] = useState(false)
  const [assigning, setAssigning] = useState(false)

  useEffect(() => {
    if (isOpen) {
      const fetchTechnicians = async () => {
        setLoading(true)
        try {
          const response = await fetch('/api/auth/users?role=TECHNICIEN', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          })
          const data = await response.json()
          setTechnicians(data.users || [])
        } catch (error) {
          toast.error('Erreur lors du chargement des techniciens')
        } finally {
          setLoading(false)
        }
      }
      fetchTechnicians()
    }
  }, [isOpen])

  const handleAssign = async () => {
    if (!selectedTech) {
      toast.error('Veuillez sélectionner un technicien')
      return
    }
    setAssigning(true)
    await onAssign(selectedTech)
    setAssigning(false)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <UserIcon className="w-5 h-5 text-indigo-600" />
            Assigner l'alerte
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <XCircleIcon className="w-6 h-6" />
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center">
            <LoadingSpinner size="md" />
          </div>
        ) : (
          <>
            <div className="space-y-3">
              <label className="block text-sm font-medium text-slate-700">
                Sélectionner un technicien
              </label>
              <select
                value={selectedTech}
                onChange={(e) => setSelectedTech(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              >
                <option value="">-- Choisir un technicien --</option>
                {technicians.map(tech => (
                  <option key={tech.id} value={tech.id}>
                    {tech.name} ({tech.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleAssign}
                disabled={assigning || !selectedTech}
                className="flex-1 rounded-lg bg-indigo-600 px-4 py-2.5 text-white font-medium hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
              >
                {assigning ? 'Assignation...' : 'Assigner'}
              </button>
              <button
                onClick={onClose}
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-slate-700 font-medium hover:bg-slate-50 transition-colors"
              >
                Annuler
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function AlertDetailPage() {
  const { alertId } = useParams()
  const [loading, setLoading] = useState(true)
  const [alert, setAlert] = useState(null)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(null)

  useEffect(() => {
    loadAlert()
  }, [alertId])

  const loadAlert = async () => {
    setLoading(true)
    try {
      const response = await getAlerteById(alertId)
      setAlert(response.data?.alert || null)
    } catch (error) {
      toast.error(error.response?.data?.error || "Impossible de charger le detail de l'alerte")
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action, payload = {}) => {
    setActionLoading(action)
    try {
      const response = await fetch(`/api/alertes/${alertId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ action, ...payload })
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Erreur lors de l\'action')
      }
      
      setAlert(data.alert)
      toast.success(`Action "${action}" effectuée avec succès`)
    } catch (error) {
      toast.error(error.message)
    } finally {
      setActionLoading(null)
    }
  }

  const handleAssign = async (technicianId) => {
    await handleAction('assign', { assigned_to: parseInt(technicianId) })
    setShowAssignModal(false)
  }

  if (loading) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-8">
        <LoadingSpinner size="lg" fullScreen={false} />
        <p className="mt-4 text-center text-slate-600">Chargement du detail...</p>
      </section>
    )
  }

  if (!alert) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
        <div className="text-center">
          <AlertIcon className="w-16 h-16 mx-auto text-slate-300 mb-3" />
          <p className="text-lg font-semibold text-slate-700">Alerte introuvable</p>
          <p className="text-sm text-slate-500 mt-1">Cette alerte n'existe pas ou a été supprimée</p>
        </div>
        <div className="flex justify-center mt-4">
          <Link to="/alertes" className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700 transition-colors">
            Retour aux alertes
          </Link>
        </div>
      </section>
    )
  }

  const canAssign = alert.status !== 'resolved'
  const canAcknowledge = !alert.acknowledged && alert.status !== 'resolved'
  const canResolve = alert.status === 'assigned' || alert.status === 'acknowledged'
  const canReopen = alert.status === 'resolved'

  return (
    <>
      <AssignModal
        isOpen={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        onAssign={handleAssign}
        currentAssignee={alert.assigned_to}
      />

      <section className="space-y-4">
        {/* Header */}
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-6 text-white shadow-xl">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <AlertIcon className="w-6 h-6" />
                <p className="text-xs uppercase tracking-wider text-slate-300 font-semibold">Détail Alerte</p>
              </div>
              <h3 className="mt-2 text-2xl font-bold sm:text-3xl">Alerte #{alert.id}</h3>
              <p className="mt-2 text-sm text-slate-300 flex items-center gap-2">
                <span className="font-semibold">{alert.machine || 'Machine'}</span>
                <span className="text-slate-400">•</span>
                <span>{alert.defect || 'Defaut detecte'}</span>
              </p>
            </div>
            <Link to="/alertes" className="rounded-lg bg-white/10 px-4 py-2.5 text-sm text-white hover:bg-white/20 transition-colors backdrop-blur-sm font-medium">
              ← Retour
            </Link>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <span className={`rounded-full border px-4 py-1.5 text-xs font-semibold ${severityStyles(alert.severity)}`}>
              {alert.severity || '-'}
            </span>
            <span className={`rounded-full border px-4 py-1.5 text-xs font-semibold ${statusStyles(alert.status)}`}>
              {alert.status || '-'}
            </span>
            <span className={`rounded-full border px-4 py-1.5 text-xs font-semibold ${alert.acknowledged ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
              {alert.acknowledged ? '✓ Acquittée' : 'Non acquittée'}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <ChartIcon className="w-4 h-4" />
            Actions rapides
          </h4>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowAssignModal(true)}
              disabled={!canAssign || actionLoading === 'assign'}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <UserIcon className="w-4 h-4" />
              {actionLoading === 'assign' ? 'Assignation...' : 'Assigner'}
            </button>
            
            <button
              onClick={() => handleAction('acknowledge')}
              disabled={!canAcknowledge || actionLoading === 'acknowledge'}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <CheckCircleIcon className="w-4 h-4" />
              {actionLoading === 'acknowledge' ? 'Acquittement...' : 'Acquitter'}
            </button>
            
            <button
              onClick={() => handleAction('resolve')}
              disabled={!canResolve || actionLoading === 'resolve'}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <CheckCircleIcon className="w-4 h-4" />
              {actionLoading === 'resolve' ? 'Résolution...' : 'Résoudre'}
            </button>
            
            <button
              onClick={() => handleAction('reopen')}
              disabled={!canReopen || actionLoading === 'reopen'}
              className="flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm text-white hover:bg-amber-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <ClockIcon className="w-4 h-4" />
              {actionLoading === 'reopen' ? 'Réouverture...' : 'Réouvrir'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main Info */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-sm">
            <h4 className="text-base font-semibold text-slate-800 flex items-center gap-2">
              <ChartIcon className="w-5 h-5 text-slate-600" />
              Informations principales
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <InfoRow label="Machine" value={alert.machine} emphasis icon={<ChartIcon className="w-3.5 h-3.5" />} />
              <InfoRow label="Defaut detecte" value={alert.defect} emphasis icon={<AlertIcon className="w-3.5 h-3.5" />} />
              <InfoRow 
                label="Score anomalie" 
                value={alert.anomaly_score !== null ? `${(alert.anomaly_score * 100).toFixed(1)}%` : (alert.defect_score !== null ? `${(alert.defect_score * 100).toFixed(1)}%` : '-')}
                icon={<ChartIcon className="w-3.5 h-3.5" />}
              />
              <InfoRow 
                label="Confiance" 
                value={alert.confidence !== null ? `${(alert.confidence * 100).toFixed(1)}%` : '-'}
                icon={<CheckCircleIcon className="w-3.5 h-3.5" />}
              />
              <InfoRow 
                label="Assigné à" 
                value={alert.assigned_to_name || alert.assigned_to || 'Non assigné'} 
                icon={<UserIcon className="w-3.5 h-3.5" />}
              />
              <InfoRow 
                label="Assigné par" 
                value={alert.assigned_by_name || alert.assigned_by || '-'} 
                icon={<UserIcon className="w-3.5 h-3.5" />}
              />
            </div>
          </div>

          {/* Timeline */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-sm">
            <h4 className="text-base font-semibold text-slate-800 flex items-center gap-2">
              <ClockIcon className="w-5 h-5 text-slate-600" />
              Chronologie
            </h4>
            <div className="space-y-3">
              <InfoRow 
                label="Créée le" 
                value={formatDate(alert.created_at)} 
                emphasis 
                icon={<ClockIcon className="w-3.5 h-3.5" />}
              />
              {alert.resolved_at && (
                <InfoRow 
                  label="Résolue le" 
                  value={formatDate(alert.resolved_at)}
                  icon={<CheckCircleIcon className="w-3.5 h-3.5" />}
                />
              )}
              {alert.validation_at && (
                <InfoRow 
                  label="Validée le" 
                  value={formatDate(alert.validation_at)}
                  icon={<CheckCircleIcon className="w-3.5 h-3.5" />}
                />
              )}
            </div>

            {/* Status Timeline */}
            <div className="mt-6 pt-4 border-t border-slate-200">
              <p className="text-xs uppercase tracking-wide text-slate-500 font-medium mb-3">Historique des statuts</p>
              <div className="space-y-2">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-green-500 mt-1.5"></div>
                  <div>
                    <p className="text-xs font-medium text-slate-700">Alerte créée</p>
                    <p className="text-xs text-slate-500">{formatDate(alert.created_at)}</p>
                  </div>
                </div>
                
                {alert.assigned_to && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>
                    <div>
                      <p className="text-xs font-medium text-slate-700">Assignée à {alert.assigned_to_name}</p>
                      <p className="text-xs text-slate-500">Par {alert.assigned_by_name}</p>
                    </div>
                  </div>
                )}
                
                {alert.acknowledged && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5"></div>
                    <div>
                      <p className="text-xs font-medium text-slate-700">Acquittée</p>
                    </div>
                  </div>
                )}
                
                {alert.status === 'resolved' && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5"></div>
                    <div>
                      <p className="text-xs font-medium text-slate-700">Résolue</p>
                      <p className="text-xs text-slate-500">{formatDate(alert.resolved_at)}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export default AlertDetailPage
