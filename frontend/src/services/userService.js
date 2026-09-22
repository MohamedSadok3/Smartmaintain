import api from './api'

export const getUsers = () => api.get('/api/users')

export const createUser = (data) => api.post('/api/users', data)

export const updateUser = (id, data) => api.patch(`/api/users/${id}`, data)

export const deleteUser = (id) => api.delete(`/api/users/${id}`)
