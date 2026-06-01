import { useNavigate, useLocation } from 'react-router-dom'
import { getUser, logout } from '../api/auth'
import { colors } from '../theme'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = getUser()

  return (
    <div style={{ borderBottom: `1px solid ${colors.borderLight}`, background: colors.white }}>
      <div style={{
        maxWidth: '100%', margin: '0 auto', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', height: 52, padding: '0 32px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
          <div onClick={() => navigate('/candidates')} style={{ cursor: 'pointer' }}>
            <span style={{ fontWeight: 700, fontSize: 16, color: colors.black, letterSpacing: '-0.3px' }}>TechKraft</span>
          </div>
          <button
            onClick={() => navigate('/candidates')}
            style={{
              padding: '6px 12px', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13,
              background: location.pathname === '/candidates' ? colors.bgHover : 'transparent',
              color: location.pathname === '/candidates' ? colors.black : colors.light,
              fontWeight: location.pathname === '/candidates' ? 500 : 400,
              transition: 'background 0.15s',
            }}
          >
            Candidates
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 13, color: colors.dark }}>
            {user?.name}
            <span style={{
              display: 'inline-block', marginLeft: 8, padding: '2px 8px',
              borderRadius: 3, fontSize: 11, fontWeight: 500,
              background: colors.bgHover, color: colors.dark,
            }}>
              {user?.role}
            </span>
          </div>
          <button
            onClick={() => { logout(); navigate('/login') }}
            style={{
              padding: '6px 12px', border: `1px solid ${colors.border}`, borderRadius: 4,
              background: colors.white, cursor: 'pointer', fontSize: 13, color: colors.mid,
              transition: 'background 0.15s, border-color 0.15s',
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}
