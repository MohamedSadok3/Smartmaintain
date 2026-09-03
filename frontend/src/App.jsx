import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import ErrorBoundary from './components/ErrorBoundary'
import LoadingSpinner from './components/LoadingSpinner'

const AlertesPage = lazy(() => import('./pages/AlertesPage'))
const AlertDetailPage = lazy(() => import('./pages/AlertDetailPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const PlantRegistrationPage = lazy(() => import('./pages/PlantRegistrationPage'))
const PlantProfilePage = lazy(() => import('./pages/PlantProfilePage'))
const ComposantsPage = lazy(() => import('./pages/ComposantsPage'))
const SurveillancePage = lazy(() => import('./pages/SurveillancePage'))
const SuperAdminPlantsPage = lazy(() => import('./pages/SuperAdminPlantsPage'))
const SuperAdminRegistrationsPage = lazy(() => import('./pages/SuperAdminRegistrationsPage'))
const UtilisateursPage = lazy(() => import('./pages/UtilisateursPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingSpinner fullScreen text="Chargement de l'application..." />}>
        <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/inscription-usine" element={<PlantRegistrationPage />} />
        <Route path="/alerte/*" element={<Navigate to="/alertes" replace />} />

        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profil" element={<ProfilePage />} />
          <Route
            path="/usine/profil"
            element={
              <RequireAuth roles={['admin']}>
                <PlantProfilePage />
              </RequireAuth>
            }
          />
          <Route
            path="/superadmin/usines"
            element={
              <RequireAuth roles={['superadmin']}>
                <SuperAdminPlantsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/superadmin/inscriptions"
            element={
              <RequireAuth roles={['superadmin']}>
                <SuperAdminRegistrationsPage />
              </RequireAuth>
            }
          />
          <Route path="/surveillance" element={<SurveillancePage />} />
          <Route
            path="/alertes"
            element={
              <RequireAuth roles={['admin', 'superviseur', 'technicien']}>
                <AlertesPage />
              </RequireAuth>
            }
          />
          <Route
            path="/alertes/:alertId"
            element={
              <RequireAuth roles={['admin', 'superviseur', 'technicien']}>
                <AlertDetailPage />
              </RequireAuth>
            }
          />
          <Route
            path="/composants"
            element={
              <RequireAuth roles={['admin']}>
                <ComposantsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/utilisateurs"
            element={
              <RequireAuth roles={['admin']}>
                <UtilisateursPage />
              </RequireAuth>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
      <Toaster position="top-right" />
    </ErrorBoundary>
  )
}

export default App
