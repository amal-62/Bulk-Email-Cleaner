import axios from 'axios'

// Create an axios instance with our backend URL as the base
// This means we can write '/emails' instead of 'http://localhost:8000/emails' everywhere
const api = axios.create({
  baseURL: 'http://localhost:8000',
})

// This runs before every request automatically
// It reads the JWT from localStorage and attaches it to the Authorization header
// So every API call is automatically authenticated
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If the backend says our token is invalid/expired, clear it and go back to
// the login page instead of leaving the user stuck on an error screen.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api
