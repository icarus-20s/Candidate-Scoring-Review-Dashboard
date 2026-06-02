import { Navigate } from 'react-router-dom'
import { isAuthenticated } from '../api/auth'

// Redirects unauthenticated users to /login, otherwise renders children.
export default function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return children
}
