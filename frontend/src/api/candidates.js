import { get, post, patch, del } from './client'

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

export async function fetchCandidate(id) {
  return get(`/candidates/${id}`)
}

export async function createCandidate(data) {
  return post('/candidates', data)
}

export async function updateCandidate(id, data) {
  return patch(`/candidates/${id}`, data)
}

export async function deleteCandidate(id) {
  return del(`/candidates/${id}`)
}

export async function submitScore(candidateId, data) {
  return post(`/candidates/${candidateId}/scores`, data)
}

export async function getScores(candidateId) {
  return get(`/candidates/${candidateId}/scores`)
}

export async function generateSummary(candidateId) {
  return post(`/candidates/${candidateId}/summary`, {})
}
