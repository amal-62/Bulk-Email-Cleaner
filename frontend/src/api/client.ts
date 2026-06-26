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

export default api