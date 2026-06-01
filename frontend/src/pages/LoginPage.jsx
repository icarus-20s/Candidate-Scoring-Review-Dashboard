import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api/auth'
import { colors } from '../theme'

export default function LoginPage() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') await login(email, password)
      else await register(email, password, name)
      navigate('/candidates')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: colors.bg }}>
      <div style={{ width: 380, background: colors.white, border: `1px solid ${colors.borderLight}`, borderRadius: 8, padding: '32px 28px' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 8, background: colors.black,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: colors.white, fontWeight: 700, fontSize: 16, margin: '0 auto 12px',
          }}>
            TK
          </div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: colors.black, marginBottom: 4 }}>TechKraft</h1>
          <p style={{ fontSize: 13, color: colors.mid }}>Candidate Scoring & Review</p>
        </div>

        <div style={{ display: 'flex', marginBottom: 20, border: `1px solid ${colors.borderLight}`, borderRadius: 4, overflow: 'hidden' }}>
          {['login', 'register'].map((m) => (
            <button
              key={m} onClick={() => setMode(m)}
              style={{
                flex: 1, padding: '8px 0', border: 'none', cursor: 'pointer', fontSize: 13,
                fontWeight: mode === m ? 500 : 400,
                background: mode === m ? colors.white : colors.bg,
                color: mode === m ? colors.black : colors.light,
              }}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: colors.dark, marginBottom: 4 }}>Name</label>
              <input
                style={{
                  width: '100%', padding: '8px 10px', border: `1px solid ${colors.border}`,
                  borderRadius: 4, fontSize: 13, outline: 'none', boxSizing: 'border-box',
                }}
                placeholder="John Doe" value={name} onChange={(e) => setName(e.target.value)} required
              />
            </div>
          )}
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: colors.dark, marginBottom: 4 }}>Email</label>
            <input
              style={{
                width: '100%', padding: '8px 10px', border: `1px solid ${colors.border}`,
                borderRadius: 4, fontSize: 13, outline: 'none', boxSizing: 'border-box',
              }}
              type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: colors.dark, marginBottom: 4 }}>Password</label>
            <input
              style={{
                width: '100%', padding: '8px 10px', border: `1px solid ${colors.border}`,
                borderRadius: 4, fontSize: 13, outline: 'none', boxSizing: 'border-box',
              }}
              type="password" placeholder="Enter password" value={password} onChange={(e) => setPassword(e.target.value)} required
            />
          </div>

          {error && (
            <div style={{
              padding: '8px 10px', background: colors.bg, border: `1px solid ${colors.border}`,
              borderRadius: 4, color: colors.dark, fontSize: 12, marginBottom: 14,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '9px 0', border: 'none', borderRadius: 4,
              background: loading ? colors.light : colors.black, color: colors.white,
              fontSize: 13, fontWeight: 500, cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Please wait...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        {mode === 'register' && (
          <p style={{ fontSize: 11, color: colors.light, textAlign: 'center', marginTop: 14 }}>
            Accounts are created as <strong>reviewer</strong> role by default.
          </p>
        )}

        {mode === 'login' && (
          <div style={{
            marginTop: 20, padding: '12px 14px', background: colors.bg,
            borderRadius: 4, fontSize: 12, color: colors.dark,
          }}>
            <div style={{ fontWeight: 500, marginBottom: 6 }}>Demo</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span>Admin:</span>
              <span style={{ fontFamily: 'monospace', fontSize: 11 }}>admin@techkraft.com / admin123</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>New user:</span>
              <span style={{ fontFamily: 'monospace', fontSize: 11 }}>register (creates reviewer role)</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
