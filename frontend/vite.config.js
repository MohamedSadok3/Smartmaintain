import react from '@vitejs/plugin-react'

export default {
  plugins: [react()],
  build: { outDir: 'dist' },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/socket.io': 'http://localhost:5000',
    },
  },
}
