import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// IMPORTANT: After deploying backend to Render, replace the URL below
// with your actual Render backend URL (e.g. https://darkai-backend.onrender.com)
const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
})
