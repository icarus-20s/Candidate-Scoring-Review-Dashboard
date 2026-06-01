import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchCandidate, submitScore, generateSummary, updateCandidate, deleteCandidate } from '../api/candidates'
import { getUser } from '../api/auth'
import useSSE from '../hooks/useSSE'
import {
  colors, badge, scoreBadge, card, input, select, label, btn, btnOutline, th,
} from '../theme'
import { CATEGORIES, STATUSES, SCORE_VALUES } from '../constants'

function fmtDate(v) {
  return new Date(v).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function avgScore(scores) {
  if (!scores.length) return null
  const avg = scores.reduce((s, x) => s + x.score, 0) / scores.length
  return Math.round(avg * 10) / 10
}

function categoryBreakdown(scores) {
  const cats = {}
  for (const s of scores) {
    if (!cats[s.category]) cats[s.category] = []
    cats[s.category].push(s.score)
  }
  return Object.entries(cats).map(([cat, vals]) => ({
    category: cat,
    avg: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length * 10) / 10,
    count: vals.length,
  }))
}

export default function CandidateDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const user = getUser()

  const [candidate, setCandidate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cat, setCat] = useState(CATEGORIES[0])
  const [score, setScore] = useState(3)
  const [note, setNote] = useState('')
  const [scoring, setScoring] = useState(false)
  const [scoreMsg, setScoreMsg] = useState(null)
  const [sumLoading, setSumLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [sumErr, setSumErr] = useState('')
  const [notes, setNotes] = useState('')
  const [notesSaving, setNotesSaving] = useState(false)
  const [notesMsg, setNotesMsg] = useState(null)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [status, setStatus] = useState('')
  const [flash, setFlash] = useState(false)
  const flashTimer = useRef(null)

  const { scores: sseScores, connected: sseConnected, updatedAt: sseUpdatedAt } = useSSE(id)

  const scores = sseScores.length > 0 ? sseScores : (candidate?.scores || [])
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    if (sseUpdatedAt) {
      setFlash(true)
      if (flashTimer.current) clearTimeout(flashTimer.current)
      flashTimer.current = setTimeout(() => setFlash(false), 2000)
    }
    return () => { if (flashTimer.current) clearTimeout(flashTimer.current) }
  }, [sseUpdatedAt])

  useEffect(() => { load() }, [id])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const d = await fetchCandidate(id)
      setCandidate(d)
      setSummary(d.ai_summary || '')
      setNotes(d.internal_notes || '')
      setStatus(d.status || '')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleScore(e) {
    e.preventDefault()
    setScoring(true)
    setScoreMsg(null)
    try {
      await submitScore(id, { category: cat, score, note })
      setScoreMsg({ type: 'ok', text: 'Score submitted.' })
      setNote('')
    } catch (err) {
      setScoreMsg({ type: 'err', text: err.message })
    } finally {
      setScoring(false)
    }
  }

  async function handleSummary() {
    setSumLoading(true)
    setSumErr('')
    setSummary('')
    try {
      const d = await generateSummary(id)
      setSummary(d.summary)
    } catch (err) {
      setSumErr(err.message)
    } finally {
      setSumLoading(false)
    }
  }

  async function handleStatusChange(newStatus) {
    setStatusUpdating(true)
    try {
      const d = await updateCandidate(id, { status: newStatus })
      setStatus(d.status)
      setCandidate(p => ({ ...p, status: d.status }))
    } catch (err) {
      console.error(err)
    } finally {
      setStatusUpdating(false)
    }
  }

  async function handleSaveNotes() {
    setNotesSaving(true)
    setNotesMsg(null)
    try {
      await updateCandidate(id, { internal_notes: notes })
      setNotesMsg({ type: 'ok', text: 'Saved.' })
    } catch (err) {
      setNotesMsg({ type: 'err', text: err.message })
    } finally {
      setNotesSaving(false)
    }
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: colors.light, fontSize: 13 }}>Loading...</div>
  if (error || !candidate) return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ fontSize: 13, color: colors.dark, marginBottom: 12 }}>{error || 'Not found'}</p>
      <button onClick={() => navigate('/candidates')} style={btnOutline}>Back</button>
    </div>
  )

  const avg = avgScore(scores)
  const breakdown = categoryBreakdown(scores)

  const thC = { ...th, padding: '8px 12px' }
  const tdC = { padding: '8px 12px', borderBottom: `1px solid ${colors.borderLight}`, fontSize: 13 }

  return (
    <div>
      <button onClick={() => navigate('/candidates')} style={{ ...btnOutline, marginBottom: 16 }}>
        &larr; Back to Candidates
      </button>

      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 600, color: colors.black, margin: 0 }}>{candidate.name}</h1>
            <div style={{ color: colors.mid, fontSize: 13, marginTop: 6, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span>{candidate.email}</span>
              <span style={{ color: colors.border }}>|</span>
              <span>{candidate.role_applied}</span>
              {isAdmin ? (
                <select value={status} onChange={(e) => handleStatusChange(e.target.value)} disabled={statusUpdating}
                  style={{
                    ...select, width: 'auto', padding: '2px 6px', fontSize: 11, fontWeight: 500,
                    cursor: 'pointer',
                  }}>
                  {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              ) : (
                <span style={badge(status)}>{status}</span>
              )}
            </div>
          </div>
          <span style={{ fontSize: 11, color: colors.light, fontFamily: 'monospace' }}>#{candidate.id}</span>
        </div>
        {candidate.skills?.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
            {candidate.skills.map(s => (
              <span key={s} style={{
                padding: '3px 10px', background: colors.bgHover, borderRadius: 4,
                fontSize: 12, color: colors.dark, border: `1px solid ${colors.borderLight}`,
              }}>{s}</span>
            ))}
          </div>
        )}
        {isAdmin && (
          <div style={{ marginTop: 16, paddingTop: 14, borderTop: `1px solid ${colors.borderLight}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: colors.light }}>Soft-deletes — sets status to archived</span>
            <button onClick={async () => {
              if (!window.confirm('Delete this candidate? This will archive them.')) return
              try {
                await deleteCandidate(id)
                navigate('/candidates')
              } catch (err) { alert(err.message) }
            }} style={{ padding: '6px 14px', border: `1px solid ${colors.border}`, borderRadius: 4, background: colors.white, cursor: 'pointer', fontSize: 12, color: colors.dark }}>
              Delete Candidate
            </button>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={card}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.black, margin: 0 }}>Scores</h2>
              {scores.length > 0 && (
                <span style={{ fontSize: 12, color: colors.mid }}>{scores.length} review{scores.length !== 1 ? 's' : ''}</span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {flash && (
                <span style={{
                  padding: '2px 8px', borderRadius: 3, fontSize: 10, fontWeight: 500,
                  background: colors.bgHover, color: colors.dark,
                }}>
                  updated
                </span>
              )}
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: sseConnected ? colors.dark : colors.light,
                display: 'inline-block',
              }} title={sseConnected ? 'Live' : 'Disconnected'} />
            </div>
          </div>

          {avg !== null && (
            <div style={{
              display: 'flex', gap: 16, marginBottom: 16, padding: '10px 14px',
              background: colors.bg, borderRadius: 6, border: `1px solid ${colors.borderLight}`,
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: colors.black, lineHeight: 1.2 }}>{avg}</div>
                <div style={{ fontSize: 10, color: colors.mid, textTransform: 'uppercase', letterSpacing: '0.3px' }}>Average</div>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                {breakdown.map(b => (
                  <div key={b.category} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: colors.dark, lineHeight: 1.3 }}>{b.avg}</div>
                    <div style={{ fontSize: 9, color: colors.mid, whiteSpace: 'nowrap' }}>{b.category}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {scores.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ ...thC, width: 28 }}>#</th>
                  <th style={thC}>Category</th>
                  <th style={{ ...thC, width: 50, textAlign: 'center' }}>Score</th>
                  {isAdmin && <th style={thC}>Reviewer</th>}
                  <th style={thC}>Note</th>
                  <th style={{ ...thC, width: 120 }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {scores.map((s, i) => (
                  <tr key={s.id} style={{ background: i % 2 === 0 ? colors.white : colors.bgHover }}
                    onMouseEnter={(e) => e.currentTarget.style.background = colors.bgHover}
                    onMouseLeave={(e) => e.currentTarget.style.background = i % 2 === 0 ? colors.white : colors.bgHover}>
                    <td style={{ ...tdC, color: colors.light, fontSize: 11 }}>{scores.length - i}</td>
                    <td style={{ ...tdC, color: colors.dark, fontWeight: 500 }}>{s.category}</td>
                    <td style={{ ...tdC, textAlign: 'center' }}>
                      <span style={scoreBadge(s.score)}>{s.score}/5</span>
                    </td>
                    {isAdmin && (
                      <td style={{ ...tdC, color: colors.mid }}>{s.reviewer_name}</td>
                    )}
                    <td style={{ ...tdC, color: colors.mid, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.note || '-'}</td>
                    <td style={{ ...tdC, fontSize: 12, color: colors.light, whiteSpace: 'nowrap' }}>{fmtDate(s.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ fontSize: 13, color: colors.light, margin: 0 }}>No scores yet. Use the form to submit the first review.</p>
          )}
        </div>

        <div>
          <div style={card}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.black, margin: '0 0 14px' }}>Submit Score</h2>
            <form onSubmit={handleScore}>
              <div style={{ marginBottom: 14 }}>
                <label style={label}>Category</label>
                <select value={cat} onChange={(e) => setCat(e.target.value)} style={select}>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={label}>Score</label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {SCORE_VALUES.map(v => (
                    <div key={v} onClick={() => setScore(v)} className={`score-btn${score === v ? ' active' : ''}`} style={{
                      width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      borderRadius: 4, fontSize: 14, fontWeight: 600, cursor: 'pointer',
                      border: `1px solid ${score === v ? colors.black : colors.border}`,
                      background: score === v ? colors.black : colors.white,
                      color: score === v ? colors.white : colors.dark,
                      transition: 'all 0.15s',
                    }}>{v}</div>
                  ))}
                </div>
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={label}>Note (optional)</label>
                <input style={input} placeholder="Add a note about this score..." value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <button type="submit" disabled={scoring} style={btn(scoring ? colors.light : colors.black)}>
                  {scoring ? 'Saving...' : 'Submit Score'}
                </button>
                {scoreMsg && <span style={{
                  fontSize: 12, color: colors.dark,
                }}>{scoreMsg.text}</span>}
              </div>
            </form>
          </div>

          <div style={card}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.black, margin: 0 }}>AI Summary</h2>
              <button onClick={handleSummary} disabled={sumLoading} style={btnOutline}>
                {sumLoading ? 'Generating...' : 'Generate'}
              </button>
            </div>
            <p style={{ fontSize: 12, color: colors.mid, margin: '0 0 12px' }}>
              Evaluates the candidate based on all scores and profile data.
            </p>
            {sumErr && <div style={{ marginBottom: 8, fontSize: 12, color: colors.dark }}>{sumErr}</div>}
            {summary && (
              <div style={{
                padding: 12, background: colors.bg, borderRadius: 4,
                fontSize: 13, lineHeight: 1.6, color: colors.dark, border: `1px solid ${colors.borderLight}`,
              }}>
                {summary}
              </div>
            )}
            {sumLoading && (
              <div style={{ padding: 12, textAlign: 'center', fontSize: 12, color: colors.light }}>Generating summary...</div>
            )}
          </div>
        </div>
      </div>

      {isAdmin && (
        <div style={{ ...card, borderLeft: `3px solid ${colors.mid}`, marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.black, margin: 0 }}>Internal Notes</h2>
            <span style={{
              padding: '1px 8px', borderRadius: 3, fontSize: 10, fontWeight: 600,
              background: colors.bgHover, color: colors.dark, textTransform: 'uppercase', letterSpacing: '0.3px',
            }}>Admin</span>
          </div>
          <textarea
            style={{ ...input, minHeight: 80, resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.5 }}
            value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Internal notes (admin only)..."
          />
          <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
            <button onClick={handleSaveNotes} disabled={notesSaving} style={btn(notesSaving ? colors.light : colors.black)}>
              {notesSaving ? 'Saving...' : 'Save'}
            </button>
            {notesMsg && <span style={{
              fontSize: 12, color: colors.dark,
            }}>{notesMsg.text}</span>}
          </div>
        </div>
      )}
    </div>
  )
}
