import { get, post, patch, del } from './client'

// Fetches the candidate list with optional filter/pagination params. Returns { items, total, page, page_size, next_offset }.
export async function fetchCandidates(params = {}) {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.role_applied) query.set('role_applied', params.role_applied)
  if (params.skill) query.set('skill', params.skill)
  if (params.keyword) query.set('keyword', params.keyword)
  if (params.offset !== undefined) query.set('offset', params.offset)
  if (params.page_size) query.set('page_size', params.page_size)

  const qs = query.toString()
  return get(`/candidates${qs ? `?${qs}` : ''}`)
}

// Fetches full candidate detail including scores and AI summary.
export async function fetchCandidate(id) {
  return get(`/candidates/${id}`)
}

// Creates a new candidate record.
export async function createCandidate(data) {
  return post('/candidates', data)
}

// Updates candidate fields (status, internal_notes, etc.).
export async function updateCandidate(id, data) {
  return patch(`/candidates/${id}`, data)
}

// Soft-deletes a candidate (admin only).
export async function deleteCandidate(id) {
  return del(`/candidates/${id}`)
}

// Submits a score for a candidate in a specific category.
export async function submitScore(candidateId, data) {
  return post(`/candidates/${candidateId}/scores`, data)
}

// Retrieves scores for a candidate (role-filtered server-side).
export async function getScores(candidateId) {
  return get(`/candidates/${candidateId}/scores`)
}

// Triggers mock AI summary generation (2s delay).
export async function generateSummary(candidateId) {
  return post(`/candidates/${candidateId}/summary`, {})
}
