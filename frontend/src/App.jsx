import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CandidateListPage from './pages/CandidateListPage'
import CandidateDetailPage from './pages/CandidateDetailPage'
import { getUser } from './api/auth'

// Root component: renders navbar when authenticated, defines routes for login, candidate list, and candidate detail.
export default function App() {
  const user = getUser()
  return (
    <div>
      {user && <Navbar />}
      <div style={{ maxWidth: '100%', margin: '0 auto', padding: user ? '24px 32px' : 0 }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/candidates" element={<ProtectedRoute><CandidateListPage /></ProtectedRoute>} />
          <Route path="/candidates/:id" element={<ProtectedRoute><CandidateDetailPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/candidates" replace />} />
        </Routes>
      </div>
    </div>
  )
}
