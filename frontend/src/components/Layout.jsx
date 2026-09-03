import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { logout } from '../services/authService'
import { getAlertes } from '../services/alerteService'
import { connectSocket } from '../services/socketService'
import { getStoredUser } from '../utils/storage'

const navItems = [
  { label: 'Tableau de bord', path: '/dashboard', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Surveillance en direct', path: '/surveillance', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Alertes', path: '/alertes', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Composants', path: '/composants', roles: ['admin'] },
  { label: 'Configuration IoT', path: '/iot/config', roles: ['admin'] },
  { label: 'Gestion utilisateurs', path: '/utilisateurs', roles: ['admin'] },
  { label: "Profil de l'usine", path: '/usine/profil', roles: ['admin'] },
  { label: 'Mon profil', path: '/profil', roles: ['admin', 'superviseur', 'technicien', 'superadmin'] },
  { label: 'Profils usines', path: '/superadmin/usines', roles: ['superadmin'] },
  { label: 'Validation usines', path: '/superadmin/inscriptions', roles: ['superadmin'] },
]

const titles = {
  '/dashboard': 'Tableau de bord',
  '/surveillance': 'Surveillance en direct',
  '/alertes': 'Alertes',
  '/composants': 'Composants',
  '/iot/config': 'Configuration IoT',
  '/utilisateurs': 'Gestion des utilisateurs',
  '/usine/profil': "Profil de l'usine",
  '/profil': 'Mon profil',
  '/superadmin/usines': 'Profils usines',
  '/superadmin/inscriptions': 'Validation usines',
}

const EMPTY_MACHINES = []

function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const pageTitle = useMemo(() => {
    if (titles[location.pathname]) return titles[location.pathname]
    if (location.pathname.startsWith('/alertes/')) return "Détail de l'alerte"
    return 'SmartMaintain'
  }, [location.pathname])

  const user = useMemo(() => getStoredUser() || { name: 'Utilisateur', role: 'technicien' }, [])
  const userMachines = user.machines || EMPTY_MACHINES
  const [hasNewAlerts, setHasNewAlerts] = useState(localStorage.getItem('hasNewAlerts') === 'true')
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const bellRef = useRef(null)

  const visibleNavItems = useMemo(
    () => navItems.filter((item) => item.roles.includes(user.role)),
    [user.role],
  )

  const canOpenAlerts = useMemo(
    () => ['admin', 'superviseur', 'technicien'].includes(user.role),
    [user.role],
  )

  useEffect(() => {
    if (!sidebarOpen) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [sidebarOpen])

  const buildNotification = useCallback((alert) => {
    if (!alert) return null
    const isManager = user.role === 'admin' || user.role === 'superviseur'
    const isTechnicien = user.role === 'technicien'

    if (isManager) {
      if (!alert.assigned_to && (alert.status === 'open' || alert.status === 'reopened')) {
        return {
          key: `${alert.id}-unassigned`,
          alertId: alert.id,
          title: 'Nouvelle alerte non assignée',
          subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Défaut détecté'}`,
        }
      }

      if (alert.acknowledged && alert.status === 'acknowledged') {
        return {
          key: `${alert.id}-validation`,
          alertId: alert.id,
          title: 'Alerte acquittée à valider',
          subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Validation requise'}`,
        }
      }
    }

    if (isTechnicien && alert.assigned_to === user.id && !alert.acknowledged) {
      return {
        key: `${alert.id}-assigned`,
        alertId: alert.id,
        title: 'Nouvelle alerte assignée',
        subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Intervention demandée'}`,
      }
    }

    return null
  }, [user.id, user.role])

  const syncHasAlerts = useCallback((items) => {
    const hasItems = items.length > 0
    localStorage.setItem('hasNewAlerts', hasItems ? 'true' : 'false')
    setHasNewAlerts(hasItems)
  }, [])

  const upsertNotification = useCallback((alert) => {
    const candidate = buildNotification(alert)
    setNotifications((prev) => {
      const withoutAlert = prev.filter((item) => item.alertId !== alert.id)
      if (!candidate) {
        syncHasAlerts(withoutAlert)
        return withoutAlert
      }
      const updated = [candidate, ...withoutAlert].slice(0, 8)
      syncHasAlerts(updated)
      return updated
    })
  }, [buildNotification, syncHasAlerts])

  useEffect(() => {
    let cancelled = false
    const loadNotifications = async () => {
      try {
        const response = await getAlertes({ page: 1, limit: 50 })
        const alerts = response.data?.alerts || []
        const items = alerts.map(buildNotification).filter(Boolean).slice(0, 8)
        if (!cancelled) {
          setNotifications(items)
          syncHasAlerts(items)
        }
      } catch {
        // Silent fallback: realtime socket updates keep notifications fresh.
      }
    }

    loadNotifications()
    const timer = window.setInterval(loadNotifications, 30000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [buildNotification, syncHasAlerts])

  useEffect(() => {
    const hasMachineAccess = (machine) => userMachines.includes(machine)
    const isRelevantAlert = (alert) => {
      if (!alert) return false
      if (user.role === 'admin' || user.role === 'superviseur') {
        return (
          (!alert.assigned_to && (alert.status === 'open' || alert.status === 'reopened')) ||
          (alert.acknowledged && alert.status === 'acknowledged')
        )
      }
      if (user.role === 'technicien') {
        return alert.assigned_to === user.id || hasMachineAccess(alert.machine)
      }
      return false
    }

    const socket = connectSocket()
    const onAlertNew = (alert) => {
      if (isRelevantAlert(alert)) {
        upsertNotification(alert)
      }
    }

    const onAlertUpdated = (alert) => {
      upsertNotification(alert)
    }

    socket.on('alert:new', onAlertNew)
    socket.on('alert:updated', onAlertUpdated)

    return () => {
      socket.off('alert:new', onAlertNew)
      socket.off('alert:updated', onAlertUpdated)
    }
  }, [upsertNotification, user.id, user.role, userMachines])

  useEffect(() => {
    const onDocumentClick = (event) => {
      if (!bellRef.current?.contains(event.target)) {
        setShowNotifications(false)
      }
    }
    document.addEventListener('click', onDocumentClick)
    return () => document.removeEventListener('click', onDocumentClick)
  }, [])

  const onBellClick = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setShowNotifications((prev) => !prev)
  }

  const openAlertDetails = (alertId) => {
    setShowNotifications(false)
    if (canOpenAlerts) {
      navigate(`/alertes/${alertId}`)
    }
  }

  const clearNotifications = () => {
    setNotifications([])
    syncHasAlerts([])
    setShowNotifications(false)
  }

  return (
    <div className="min-h-screen flex bg-[#e2e8f0] lg:h-screen">
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fermer le menu"
          className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[min(280px,85vw)] flex-col bg-[#0f172a] text-slate-100 shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:w-60 lg:min-w-[240px] lg:max-w-[240px] lg:translate-x-0 lg:shadow-none ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between border-b border-slate-700 px-4 py-5 lg:px-5 lg:py-6">
          <div className="space-y-1">
            <h1 className="text-lg font-semibold text-[#16a34a] sm:text-xl">SmartMaintain</h1>
            <p className="text-xs text-slate-400">Suite IA Industrielle</p>
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 lg:hidden"
            aria-label="Fermer le menu"
            onClick={() => setSidebarOpen(false)}
          >
            ✕
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3 lg:p-4">
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2.5 text-sm transition sm:px-4 ${
                  isActive
                    ? 'bg-[#16a34a] text-white shadow'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-700 p-4">
          <p className="truncate text-sm font-medium">{user.name}</p>
          <span className="mt-2 inline-block rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-200">
            {user.role}
          </span>
          <button
            type="button"
            onClick={logout}
            className="mt-3 w-full rounded-md bg-slate-800 px-3 py-2 text-xs text-slate-200 hover:bg-slate-700"
          >
            Deconnexion
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen min-w-0 flex-1 flex-col lg:min-h-0">
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 sm:h-16 sm:px-6">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <button
              type="button"
              className="rounded-lg border border-slate-200 p-2 text-slate-700 hover:bg-slate-50 lg:hidden"
              aria-label="Ouvrir le menu"
              onClick={() => setSidebarOpen(true)}
            >
              <span className="sr-only">Menu</span>
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
            <h2 className="truncate text-base font-semibold text-slate-800 sm:text-xl">{pageTitle}</h2>
          </div>

          <div className="relative shrink-0" ref={bellRef}>
            <button
              type="button"
              onClick={onBellClick}
              className="relative rounded-full p-2 text-slate-600 hover:bg-slate-100"
              aria-label="Notifications"
            >
              <span className="text-lg">🔔</span>
              {hasNewAlerts && <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-red-500" />}
            </button>

            {showNotifications && (
              <div className="absolute right-0 z-50 mt-2 w-[min(20rem,calc(100vw-2rem))] rounded-xl border border-slate-200 bg-white shadow-xl">
                <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
                  <p className="text-sm font-semibold text-slate-700">Notifications</p>
                  <button
                    type="button"
                    onClick={clearNotifications}
                    className="text-xs text-slate-500 hover:text-slate-700"
                  >
                    Tout marquer lu
                  </button>
                </div>

                <div className="max-h-72 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="px-3 py-4 text-sm text-slate-500">Aucune nouvelle notification.</p>
                  ) : (
                    notifications.map((item) => (
                      <button
                        type="button"
                        key={item.key}
                        onClick={() => openAlertDetails(item.alertId)}
                        className="w-full border-b border-slate-100 px-3 py-2 text-left hover:bg-slate-50"
                      >
                        <p className="text-sm font-medium text-slate-800">{item.title}</p>
                        <p className="text-xs text-slate-500">{item.subtitle}</p>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
