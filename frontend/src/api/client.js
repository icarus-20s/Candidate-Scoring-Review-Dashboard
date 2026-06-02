export const API_BASE = '/api'

// Core request helper: attaches JWT auth header, parses JSON response, normalizes errors.
async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (resp.status === 204) return null

  let data
  try {
    data = await resp.json()
  } catch {
    throw new Error(resp.ok ? 'Empty response from server' : `Server error (${resp.status}) — is the backend running?`)
  }

  if (!resp.ok) {
    throw new Error(data.detail || `Request failed: ${resp.status}`)
  }

  return data
}

// Sends a GET request to the given API path.
export function get(path) {
  return request(path, { method: 'GET' })
}

// Sends a POST request with a JSON body.
export function post(path, body) {
  return request(path, { method: 'POST', body: JSON.stringify(body) })
}

// Sends a PATCH request with a JSON body.
export function patch(path, body) {
  return request(path, { method: 'PATCH', body: JSON.stringify(body) })
}

// Sends a DELETE request.
export function del(path) {
  return request(path, { method: 'DELETE' })
}
