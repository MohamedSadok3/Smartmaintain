import { Navigate, useLocation } from 'react-router-dom'
import { getStoredUser } from '../utils/storage'

function RequireAuth({ children, roles = [] }) {
  const location = useLocation()
  const token = localStorage.getItem('token')

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  const user = getStoredUser()

  if (roles.length > 0 && !roles.includes(user?.role)) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default RequireAuth
