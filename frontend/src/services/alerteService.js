import api from './api'

export const getAlertes = (params) => api.get('/api/alertes', { params })
export const getAlerteById = (id) => api.get(`/api/alertes/${id}`)

export const assignAlert = (id, userId) =>
  api.patch(`/api/alertes/${id}`, {
    assigned_to: userId,
  })

export const resolveAlert = (id) =>
  api.patch(`/api/alertes/${id}`, {
    status: 'resolved',
  })

export const reopenAlert = (id) =>
  api.patch(`/api/alertes/${id}`, {
    status: 'reopened',
  })

export const acknowledgeAlert = (id) =>
  api.patch(`/api/alertes/${id}`, {
    acknowledged: true,
  })
