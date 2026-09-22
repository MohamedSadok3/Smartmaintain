import { io } from 'socket.io-client'
import { SOCKET_URL } from './api'

// Singleton socket instance — one connection shared across the whole app.
let socket = null

function createSocket() {
  return io(SOCKET_URL, {
    // Use a callback so the token is read fresh at connect time (not at creation).
    auth: (callback) => callback({ token: localStorage.getItem('token') }),
    transports: ['websocket', 'polling'],
    autoConnect: false,
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
  })
}

export function getSocket() {
  if (!socket) {
    socket = createSocket()
  }
  return socket
}

/**
 * Call this after a successful login so the socket reconnects
 * with the newly stored token and joins the correct plant room.
 */
export function resetSocket() {
  if (socket) {
    socket.disconnect()
    socket.removeAllListeners()
    socket = null
  }
  // New instance will read the fresh token via the auth callback on connect.
  socket = createSocket()
  return socket
}

export function connectSocket() {
  const currentSocket = getSocket()
  console.log('[Socket] connectSocket called, connected=', currentSocket.connected, 'url=', SOCKET_URL)
  if (!currentSocket.connected) {
    currentSocket.connect()
    currentSocket.on('connect', () => console.log('[Socket] connected! id=', currentSocket.id))
    currentSocket.on('connect_error', (err) => console.error('[Socket] connect_error:', err.message, err))
    currentSocket.on('disconnect', (reason) => console.warn('[Socket] disconnected:', reason))
  }
  return currentSocket
}
