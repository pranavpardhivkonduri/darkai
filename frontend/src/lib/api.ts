import axios from 'axios'

// In production (Vercel), API calls go directly to the Render backend.
// In development, Vite proxy handles /api -> localhost:8000.
const baseURL = import.meta.env.VITE_BACKEND_URL
  ? `${import.meta.env.VITE_BACKEND_URL}/api/v1`
  : '/api/v1'

const api = axios.create({
  baseURL,
  timeout: 60000,
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('darkai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      const path = window.location.pathname
      if (path !== '/login' && path !== '/mfa') {
        localStorage.removeItem('darkai_token')
        localStorage.removeItem('darkai_user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
