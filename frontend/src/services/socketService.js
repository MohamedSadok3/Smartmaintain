import { io } from 'socket.io-client'
import { SOCKET_URL } from './api'

// Singleton socket instance — one connection shared across the whole app.
// Creating a new io() on every hook mount caused multiple overlapping
// connections that flooded each other and starved the real-time feed.
let socket = null

export function getSocket() {
  if (!socket) {
    socket = io(SOCKET_URL, {
      auth: (callback) => callback({ token: localStorage.getItem('token') }),
      transports: ['websocket', 'polling'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
    })
  }
  return socket
}

export function connectSocket() {
  const currentSocket = getSocket()
  if (!currentSocket.connected) currentSocket.connect()
  return currentSocket
}
