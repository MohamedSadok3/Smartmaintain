import api from './api'
import { clearSession, getStoredUser } from '../utils/storage'

// Auth
export const login = (email, password) => api.post('/api/auth/login', { email, password })

export const logout = () => {
  clearSession()
  window.location.href = '/login'
}

export const getUser = () => getStoredUser()
export const getMe = () => api.get('/api/auth/me')
export const updateProfile = (payload) => api.patch('/api/auth/me', payload)

// Plant registration flow
export const registerPlant = (payload) => api.post('/api/auth/register-plant', payload)

// Superadmin: registration reviews
export const getRegistrations = (params) => api.get('/api/auth/registrations', { params })
export const reviewRegistration = (id, payload) =>
  api.patch(`/api/auth/registrations/${id}/review`, payload)

// Admin: own plant
export const getMyPlant = () => api.get('/api/plants/me')
export const updateMyPlant = (payload) => api.patch('/api/plants/me', payload)

// Superadmin: all plants
export const getPlants = (params) => api.get('/api/plants', { params })
export const deletePlant = (id) => api.delete(`/api/plants/${id}`)
export const getPlantOverview = (id) => api.get(`/api/plants/${id}/overview`)
