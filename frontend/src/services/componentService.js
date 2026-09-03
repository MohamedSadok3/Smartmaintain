import api from './api'

export const getComponents = () => api.get('/api/components')

export const createComponent = (data) => api.post('/api/components', data)

export const updateComponent = (id, data) => api.patch(`/api/components/${id}`, data)

export const deleteComponent = (id) => api.delete(`/api/components/${id}`)
