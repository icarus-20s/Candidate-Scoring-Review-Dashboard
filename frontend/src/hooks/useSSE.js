import { useState, useEffect, useRef } from 'react'
import { API_BASE } from '../api/client'

export default function useSSE(candidateId) {
  const [scores, setScores] = useState([])
  const [connected, setConnected] = useState(false)
  const [updatedAt, setUpdatedAt] = useState(null)
  const esRef = useRef(null)

  useEffect(() => {
    if (!candidateId) return

    const token = localStorage.getItem('token')
    if (!token) return

    const url = `${API_BASE}/candidates/${candidateId}/stream?token=${token}`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => setConnected(true)

    es.addEventListener('score_update', (event) => {
      try {
        const data = JSON.parse(event.data)
        setScores(data)
        setUpdatedAt(Date.now())
      } catch (err) {
        console.error('SSE parse error:', err)
      }
    })

    es.onerror = () => {
      setConnected(false)
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [candidateId])

  return { scores, connected, updatedAt }
}
