import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCandidates, createCandidate } from '../api/candidates'
import { colors, badge, th, td, btnOutline, btn, paginationBtn, input, select, label } from '../theme'
import { STATUSES, PAGE_SIZE } from '../constants'

const FILTERS = [
  { key: 'status', placeholder: 'All status', type: 'select' },
  { key: 'role_applied', placeholder: 'Role', type: 'text' },
  { key: 'skill', placeholder: 'Skill', type: 'text' },
  { key: 'keyword', placeholder: 'Keyword', type: 'text' },
]

export default function CandidateListPage() {
  const navigate = useNavigate()
  const [candidates, setCandidates] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filters, setFilters] = useState({ status: '', role_applied: '', skill: '', keyword: '' })
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', role_applied: '', skills: '' })
  const [creating, setCreating] = useState(false)
  const [createErr, setCreateErr] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { offset, page_size: PAGE_SIZE }
      FILTERS.forEach(({ key }) => { if (filters[key]) params[key] = filters[key] })
      const data = await fetchCandidates(params)
      setCandidates(data.items)
      setTotal(data.total)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }, [offset, filters])

  useEffect(() => { load() }, [load])

  const hasFilters = Object.values(filters).some(v => v !== '')

  async function handleCreate(e) {
    e.preventDefault()
    setCreating(true)
    setCreateErr('')
    try {
      const skills = form.skills.split(',').map(s => s.trim()).filter(Boolean)
      await createCandidate({ ...form, skills })
      setShowCreate(false)
      setForm({ name: '', email: '', role_applied: '', skills: '' })
      setOffset(0)
      load()
    } catch (err) {
      setCreateErr(err.message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: colors.black, margin: 0 }}>Candidates</h1>
        <button onClick={() => setShowCreate(!showCreate)} style={btnOutline}>
          {showCreate ? 'Cancel' : '+ New Candidate'}
        </button>
      </div>

      {showCreate && (
        <div style={{ background: colors.white, border: `1px solid ${colors.borderLight}`, borderRadius: 8, padding: 20, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.black, margin: '0 0 14px' }}>Add Candidate</h2>
          <form onSubmit={handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
              <div>
                <label style={label}>Name</label>
                <input style={input} placeholder="Full name" value={form.name}
                  onChange={(e) => setForm(p => ({ ...p, name: e.target.value }))} required />
              </div>
              <div>
                <label style={label}>Email</label>
                <input style={input} type="email" placeholder="Email" value={form.email}
                  onChange={(e) => setForm(p => ({ ...p, email: e.target.value }))} required />
              </div>
              <div>
                <label style={label}>Role Applied</label>
                <input style={input} placeholder="e.g. Frontend Engineer" value={form.role_applied}
                  onChange={(e) => setForm(p => ({ ...p, role_applied: e.target.value }))} required />
              </div>
              <div>
                <label style={label}>Skills (comma-separated)</label>
                <input style={input} placeholder="React, TypeScript, CSS" value={form.skills}
                  onChange={(e) => setForm(p => ({ ...p, skills: e.target.value }))} />
              </div>
            </div>
            {createErr && <p style={{ fontSize: 12, color: colors.dark, margin: '0 0 10px' }}>{createErr}</p>}
            <button type="submit" disabled={creating} style={btn(creating ? colors.light : colors.black)}>
              {creating ? 'Adding...' : 'Add Candidate'}
            </button>
          </form>
        </div>
      )}

      <div style={{ background: colors.white, border: `1px solid ${colors.borderLight}`, borderRadius: 8 }}>
        <div style={{ padding: '12px 24px', borderBottom: `1px solid ${colors.borderLight}`, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {FILTERS.map(({ key, placeholder, type }) =>
            type === 'select' ? (
              <select key={key} value={filters[key]}
                onChange={(e) => { setFilters(p => ({ ...p, [key]: e.target.value })); setOffset(0) }}
                style={{ padding: '6px 10px', border: `1px solid ${colors.border}`, borderRadius: 4, fontSize: 12, background: colors.white, color: colors.dark, outline: 'none' }}>
                <option value="">{placeholder}</option>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            ) : (
              <input key={key} placeholder={placeholder} value={filters[key]}
                onChange={(e) => { setFilters(p => ({ ...p, [key]: e.target.value })); setOffset(0) }}
                style={{ padding: '6px 10px', border: `1px solid ${colors.border}`, borderRadius: 4, fontSize: 12, outline: 'none', minWidth: 110 }} />
            )
          )}
          {hasFilters && (
            <button onClick={() => { setFilters({ status: '', role_applied: '', skill: '', keyword: '' }); setOffset(0) }} style={btnOutline}>
              Clear
            </button>
          )}
        </div>

        {loading ? (
          <div style={{ padding: '40px 24px', textAlign: 'center', color: colors.light, fontSize: 13 }}>Loading...</div>
        ) : candidates.length === 0 ? (
          <div style={{ padding: '40px 24px', textAlign: 'center', color: colors.light, fontSize: 13 }}>No candidates found.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Name', 'Email', 'Role', 'Status', 'Skills'].map(h => (
                  <th key={h} style={th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, i) => (
                <tr key={c.id} onClick={() => navigate(`/candidates/${c.id}`)}
                  style={{ cursor: 'pointer', background: i % 2 === 0 ? colors.white : colors.bgHover }}
                  onMouseEnter={(e) => e.currentTarget.style.background = colors.bgHover}
                  onMouseLeave={(e) => e.currentTarget.style.background = i % 2 === 0 ? colors.white : colors.bgHover}>
                  <td style={{ ...td, color: colors.black, fontWeight: 500 }}>{c.name}</td>
                  <td style={{ ...td, color: colors.mid }}>{c.email}</td>
                  <td style={{ ...td, color: colors.dark }}>{c.role_applied}</td>
                  <td style={td}><span style={badge(c.status)}>{c.status}</span></td>
                  <td style={td}>
                    {(c.skills || []).map(sk => (
                      <span key={sk} style={{ padding: '1px 6px', background: colors.bgHover, borderRadius: 3, fontSize: 11, color: colors.mid, marginRight: 3 }}>
                        {sk}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {candidates.length > 0 && (
          <div style={{
            padding: '12px 24px', borderTop: `1px solid ${colors.borderLight}`,
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, fontSize: 13, color: colors.mid,
          }}>
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} style={paginationBtn(offset === 0)}>
              Previous
            </button>
            <span>{offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}</span>
            <button disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)} style={paginationBtn(offset + PAGE_SIZE >= total)}>
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}