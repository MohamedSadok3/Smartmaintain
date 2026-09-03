import axios from 'axios'
import { clearSession } from '../utils/storage'

export const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000'
export const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || GATEWAY_URL

const api = axios.create({
  baseURL: GATEWAY_URL,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearSession()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api
