import { post } from './client'

// Authenticates with email/password, stores token and user info in localStorage.
export async function login(email, password) {
  const data = await post('/auth/login', { email, password })
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  return data
}

// Registers a new reviewer account, stores token and user info in localStorage.
export async function register(email, password, name) {
  const data = await post('/auth/register', { email, password, name })
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
  return data
}

// Clears auth state from localStorage.
export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

// Returns the parsed user object from localStorage, or null.
export function getUser() {
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
}

// Checks whether a JWT token exists in localStorage.
export function isAuthenticated() {
  return !!localStorage.getItem('token')
}
