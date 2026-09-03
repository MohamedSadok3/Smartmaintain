import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../services/api'
import { connectSocket } from '../services/socketService'
import { getUser } from '../services/authService'
import {
  acknowledgeAlert,
  assignAlert,
  getAlertes,
  reopenAlert,
  resolveAlert,
} from '../services/alerteService'
import { MACHINE_OPTIONS } from '../constants/machines'
import { AlertListSkeleton } from '../components/SkeletonLoader'
import EmptyState from '../components/EmptyState'
import { 
  AlertIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  FilterIcon,
  UserIcon,
  RefreshIcon,
  EyeIcon,
  ClockIcon
} from '../components/Icons'

const LIMIT = 20

function severityBadgeClass(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700 border-red-200'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700 border-amber-200'
  return 'bg-green-100 text-green-700 border-green-200'
}

function statusBadgeClass(status) {
  if (status === 'resolved') return 'bg-green-100 text-green-700 border-green-200'
  if (status === 'acknowledged') return 'bg-blue-100 text-blue-700 border-blue-200'
  if (status === 'assigned') return 'bg-purple-100 text-purple-700 border-purple-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function formatDateTime(inputDate) {
  if (!inputDate) return '-'
  return new Date(inputDate).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function AlertesPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const currentUser = getUser()
  const isManager = currentUser?.role === 'admin' || currentUser?.role === 'superviseur'
  const isTechnicien = currentUser?.role === 'technicien'

  const [rows, setRows] = useState([])
  const [techniciens, setTechniciens] = useState([])
  const [loading, setLoading] = useState(true)
  const [flashIds, setFlashIds] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [focusAlertId, setFocusAlertId] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedAlerts, setSelectedAlerts] = useState([])
  
  const [filters, setFilters] = useState({
    machine: '',
    severity: '',
    status: '',
    acknowledged: '',
    technician: '',
    from: '',
    to: '',
  })
  
  const isValidatedView = filters.status === 'resolved' && filters.acknowledged === 'true'
  const alertIdFromQuery = useMemo(
    () => Number(new URLSearchParams(location.search).get('alertId')) || null,
    [location.search],
  )

  const visibleRows = useMemo(() => {
    let filtered = rows
    if (isTechnicien) {
      filtered = filtered.filter((item) => item.assigned_to === currentUser?.id)
    }
    if (filters.technician) {
      filtered = filtered.filter((item) => String(item.assigned_to || '') === String(filters.technician))
    }
    return filtered
  }, [rows, isTechnicien, currentUser?.id, filters.technician])

  const pageButtons = useMemo(() => {
    const maxPage = hasNextPage ? currentPage + 1 : currentPage
    return Array.from({ length: maxPage }, (_, idx) => idx + 1)
  }, [currentPage, hasNextPage])

  const fetchAlertes = async (page = currentPage) => {
    setLoading(true)
    try {
      const params = {
        page,
        limit: LIMIT,
        machine: filters.machine || undefined,
        severity: filters.severity || undefined,
        status: filters.status || undefined,
        acknowledged: filters.acknowledged || undefined,
        from: filters.from || undefined,
        to: filters.to || undefined,
      }
      const response = await getAlertes(params)
      const alerts = response.data.alerts || []
      setRows(alerts)
      setHasNextPage(alerts.length === LIMIT)
      setCurrentPage(page)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erreur chargement alertes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlertes(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.machine,
    filters.severity,
    filters.status,
    filters.acknowledged,
    filters.from,
    filters.to,
    filters.technician,
  ])

  useEffect(() => {
    if (!alertIdFromQuery) return
    setFocusAlertId(alertIdFromQuery)
  }, [alertIdFromQuery])

  useEffect(() => {
    if (!focusAlertId) return
    const target = document.getElementById(`alert-row-${focusAlertId}`)
    if (!target) return
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    window.setTimeout(() => setFocusAlertId(null), 3500)
  }, [focusAlertId, visibleRows])

  useEffect(() => {
    if (!isManager) return
    const loadTechniciens = async () => {
      try {
        const response = await api.get('/api/users', { params: { role: 'technicien' } })
        const users = response.data.users || []
        setTechniciens(users.filter((item) => item.role === 'technicien'))
      } catch {
        toast.error('Impossible de charger les techniciens')
      }
    }
    loadTechniciens()
  }, [isManager])

  useEffect(() => {
    const socket = connectSocket()
    const onAlertNew = (incoming) => {
      setRows((prev) => [incoming, ...prev].slice(0, LIMIT))
      setFlashIds((prev) => [...prev, incoming.id])
      toast.success(`Nouvelle alerte: ${incoming.machine} - ${incoming.defect}`, {
        duration: 5000,
        icon: '🚨'
      })
      window.setTimeout(() => {
        setFlashIds((prev) => prev.filter((id) => id !== incoming.id))
      }, 2000)
    }
    const onAlertUpdated = (updated) => {
      setRows((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    }
    socket.on('alert:new', onAlertNew)
    socket.on('alert:updated', onAlertUpdated)
    return () => {
      socket.off('alert:new', onAlertNew)
      socket.off('alert:updated', onAlertUpdated)
    }
  }, [])

  const onAssign = async (alertId, value) => {
    const parsedValue = value === '' ? null : Number(value)
    try {
      await assignAlert(alertId, parsedValue)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId
            ? {
                ...item,
                assigned_to: parsedValue,
                status: parsedValue ? 'assigned' : 'open',
                acknowledged: false,
              }
            : item,
        ),
      )
      toast.success('Alerte assignée avec succès')
    } catch (error) {
      toast.error(error.response?.data?.error || "Échec d'assignation")
    }
  }

  const onResolve = async (alertId) => {
    try {
      await resolveAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId ? { ...item, status: 'resolved', acknowledged: true } : item,
        ),
      )
      toast.success('Tâche validée et déplacée vers alertes acquittées')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec validation')
    }
  }

  const onAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId ? { ...item, acknowledged: true, status: 'acknowledged' } : item,
        ),
      )
      toast.success('Tâche acquittée avec succès')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec acquittement')
    }
  }

  const onReopen = async (alertId) => {
    try {
      await reopenAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId
            ? {
                ...item,
                status: item.assigned_to ? 'assigned' : 'open',
                acknowledged: false,
                validation_at: null,
                resolved_at: null,
              }
            : item,
        ),
      )
      toast.success('Tâche ré-ouverte avec succès')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec ré-ouverture')
    }
  }

  // Actions rapides en lot
  const handleBulkAssign = async (technicianId) => {
    if (selectedAlerts.length === 0) {
      toast.error('Aucune alerte sélectionnée')
      return
    }
    
    const toastId = toast.loading(`Attribution de ${selectedAlerts.length} alerte(s)...`)
    try {
      await Promise.all(selectedAlerts.map(id => assignAlert(id, technicianId)))
      await fetchAlertes(currentPage)
      toast.success(`${selectedAlerts.length} alerte(s) assignée(s)`, { id: toastId })
      setSelectedAlerts([])
    } catch (error) {
      toast.error('Erreur lors de l\'attribution en lot', { id: toastId })
    }
  }

  const handleBulkAcknowledge = async () => {
    if (selectedAlerts.length === 0) {
      toast.error('Aucune alerte sélectionnée')
      return
    }
    
    const toastId = toast.loading(`Acquittement de ${selectedAlerts.length} alerte(s)...`)
    try {
      await Promise.all(selectedAlerts.map(id => acknowledgeAlert(id)))
      await fetchAlertes(currentPage)
      toast.success(`${selectedAlerts.length} alerte(s) acquittée(s)`, { id: toastId })
      setSelectedAlerts([])
    } catch (error) {
      toast.error('Erreur lors de l\'acquittement en lot', { id: toastId })
    }
  }

  const toggleSelectAlert = (alertId) => {
    setSelectedAlerts(prev => 
      prev.includes(alertId) 
        ? prev.filter(id => id !== alertId)
        : [...prev, alertId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedAlerts.length === visibleRows.length) {
      setSelectedAlerts([])
    } else {
      setSelectedAlerts(visibleRows.map(row => row.id))
    }
  }

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <AlertIcon className="w-6 h-6 text-red-600" />
              Gestion des alertes
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              {visibleRows.length} alerte(s) • {selectedAlerts.length} sélectionnée(s)
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Bouton filtres */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition"
            >
              <FilterIcon className="w-4 h-4" />
              <span className="text-sm font-medium">Filtres</span>
            </button>

            {/* Bouton refresh */}
            <button
              onClick={() => fetchAlertes(currentPage)}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
              <RefreshIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span className="text-sm font-medium">Actualiser</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filtres rapides */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: '', acknowledged: 'false' }))}
          className={`flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-medium transition-all ${
            !filters.status && filters.acknowledged === 'false'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
              : 'bg-white text-slate-700 border border-slate-200 hover:border-blue-300 hover:bg-blue-50'
          }`}
        >
          <AlertIcon className="w-4 h-4" />
          Nouvelles alertes
        </button>
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: 'acknowledged', acknowledged: 'true' }))}
          className={`flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-medium transition-all ${
            filters.status === 'acknowledged' && filters.acknowledged === 'true'
              ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
              : 'bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100'
          }`}
        >
          <ClockIcon className="w-4 h-4" />
          Tâches à valider
        </button>
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: 'resolved', acknowledged: 'true' }))}
          className={`flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-medium transition-all ${
            filters.status === 'resolved' && filters.acknowledged === 'true'
              ? 'bg-green-600 text-white shadow-lg shadow-green-600/30'
              : 'bg-green-50 text-green-700 border border-green-200 hover:bg-green-100'
          }`}
        >
          <CheckCircleIcon className="w-4 h-4" />
          Tâches validées
        </button>
      </div>

      {/* Panneau de filtres avancés */}
      {showFilters && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <FilterIcon className="w-4 h-4" />
            Filtres avancés
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Machine</label>
              <select
                value={filters.machine}
                onChange={(e) => setFilters((prev) => ({ ...prev, machine: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="">Toutes</option>
                {MACHINE_OPTIONS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Sévérité</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters((prev) => ({ ...prev, severity: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="">Toutes</option>
                <option value="Critique">Critique</option>
                <option value="Majeure">Majeure</option>
                <option value="Mineure">Mineure</option>
              </select>
            </div>

            {isManager && (
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Technicien</label>
                <select
                  value={filters.technician}
                  onChange={(e) => setFilters((prev) => ({ ...prev, technician: e.target.value }))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="">Tous</option>
                  {techniciens.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Date début</label>
              <input
                type="date"
                value={filters.from}
                onChange={(e) => setFilters((prev) => ({ ...prev, from: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Date fin</label>
              <input
                type="date"
                value={filters.to}
                onChange={(e) => setFilters((prev) => ({ ...prev, to: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>
        </div>
      )}

      {/* Actions en lot */}
      {selectedAlerts.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-blue-900">
                {selectedAlerts.length} alerte(s) sélectionnée(s)
              </span>
              <button
                onClick={() => setSelectedAlerts([])}
                className="text-xs text-blue-700 hover:text-blue-900 underline"
              >
                Tout désélectionner
              </button>
            </div>

            <div className="flex items-center gap-3">
              {isManager && (
                <div className="flex items-center gap-2">
                  <label className="text-xs font-medium text-blue-900">Assigner à:</label>
                  <select
                    onChange={(e) => e.target.value && handleBulkAssign(Number(e.target.value))}
                    className="rounded-lg border border-blue-300 px-3 py-1.5 text-sm"
                    defaultValue=""
                  >
                    <option value="">Choisir...</option>
                    {techniciens.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {isTechnicien && (
                <button
                  onClick={handleBulkAcknowledge}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium"
                >
                  <CheckCircleIcon className="w-4 h-4" />
                  Acquitter la sélection
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Contenu principal */}
      {loading ? (
        <AlertListSkeleton count={5} />
      ) : visibleRows.length === 0 ? (
        <EmptyState
          icon="✅"
          title="Aucune alerte trouvée"
          description="Modifiez vos filtres ou créez une nouvelle alerte"
        />
      ) : (
        // Vue en tableau uniquement
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr className="text-left text-slate-600 font-medium">
                  <th className="py-3 px-4">
                    <input
                      type="checkbox"
                      checked={visibleRows.length > 0 && selectedAlerts.length === visibleRows.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded border-slate-300"
                    />
                  </th>
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Machine</th>
                  <th className="py-3 px-4">Défaut</th>
                  <th className="py-3 px-4">Sévérité</th>
                  <th className="py-3 px-4">Heure</th>
                  <th className="py-3 px-4">Statut</th>
                  {isValidatedView && <th className="py-3 px-4">Assigné par</th>}
                  <th className="py-3 px-4">Assigné à</th>
                  {isValidatedView && <th className="py-3 px-4">Date validation</th>}
                  <th className="py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.map((row) => (
                  <tr
                    key={row.id}
                    id={`alert-row-${row.id}`}
                    className={`border-b border-slate-100 transition-colors duration-[2000ms] ${
                      flashIds.includes(row.id) || focusAlertId === row.id 
                        ? 'bg-green-100' 
                        : selectedAlerts.includes(row.id)
                        ? 'bg-blue-50'
                        : 'bg-white hover:bg-slate-50'
                    } cursor-pointer`}
                  >
                    <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedAlerts.includes(row.id)}
                        onChange={() => toggleSelectAlert(row.id)}
                        className="w-4 h-4 rounded border-slate-300"
                      />
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900" onClick={() => navigate(`/alertes/${row.id}`)}>
                      {row.id}
                    </td>
                    <td className="py-3 px-4 capitalize" onClick={() => navigate(`/alertes/${row.id}`)}>
                      {row.machine}
                    </td>
                    <td className="py-3 px-4" onClick={() => navigate(`/alertes/${row.id}`)}>
                      {row.defect}
                    </td>
                    <td className="py-3 px-4" onClick={() => navigate(`/alertes/${row.id}`)}>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold border ${severityBadgeClass(row.severity)}`}>
                        {row.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600" onClick={() => navigate(`/alertes/${row.id}`)}>
                      {formatDateTime(row.created_at)}
                    </td>
                    <td className="py-3 px-4" onClick={() => navigate(`/alertes/${row.id}`)}>
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${statusBadgeClass(row.status)}`}>
                        {row.status}
                      </span>
                    </td>
                    {isValidatedView && (
                      <td className="py-3 px-4" onClick={() => navigate(`/alertes/${row.id}`)}>
                        {row.assigned_by_name || '-'}
                      </td>
                    )}
                    <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                      {isManager ? (
                        <select
                          value={row.assigned_to || ''}
                          onChange={(e) => onAssign(row.id, e.target.value)}
                          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                        >
                          <option value="">Non assigné</option>
                          {techniciens.map((user) => (
                            <option key={user.id} value={user.id}>
                              {user.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span>{row.assigned_to_name || row.assigned_to || '-'}</span>
                      )}
                    </td>
                    {isValidatedView && (
                      <td className="py-3 px-4 text-slate-600" onClick={() => navigate(`/alertes/${row.id}`)}>
                        {row.validation_at ? new Date(row.validation_at).toLocaleString('fr-FR') : '-'}
                      </td>
                    )}
                    <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-2">
                        {isManager && !isValidatedView && (
                          <button
                            onClick={() => onResolve(row.id)}
                            disabled={!row.acknowledged}
                            className="flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-xs text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                          >
                            <CheckCircleIcon className="w-3 h-3" />
                            Valider
                          </button>
                        )}
                        {isManager && isValidatedView && (
                          <button
                            onClick={() => onReopen(row.id)}
                            className="flex items-center gap-1 rounded-lg bg-amber-600 px-3 py-1.5 text-xs text-white hover:bg-amber-700 transition"
                          >
                            <XCircleIcon className="w-3 h-3" />
                            Réouvrir
                          </button>
                        )}
                        {isTechnicien && (
                          <button
                            onClick={() => onAcknowledge(row.id)}
                            disabled={row.acknowledged || row.assigned_to !== currentUser?.id}
                            className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                          >
                            <CheckCircleIcon className="w-3 h-3" />
                            {row.acknowledged ? 'Acquittée' : 'Acquitter'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">
          Page {currentPage} {hasNextPage && 'sur plusieurs'}
        </p>
        <div className="flex items-center gap-2">
          {pageButtons.map((pageNumber) => (
            <button
              key={pageNumber}
              onClick={() => fetchAlertes(pageNumber)}
              className={`h-10 min-w-10 rounded-lg px-3 text-sm font-medium transition ${
                currentPage === pageNumber
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              {pageNumber}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

export default AlertesPage
