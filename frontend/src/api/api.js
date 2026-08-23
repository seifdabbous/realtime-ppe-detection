const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
export const WS_BASE_URL = (import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000').replace(/\/$/, '')

const TOKEN_KEY = 'ppe_access_token'

export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options = {}) {
  const token = tokenStore.get()
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')

  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Cannot reach the safety monitoring backend.')
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch {
      // The API did not return a JSON error body.
    }
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) return null
  return response.json()
}

async function requestBlob(path) {
  const token = tokenStore.get()
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!response.ok) throw new ApiError(`Could not load prediction result (${response.status}).`, response.status)
    return response.blob()
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError('Cannot reach the safety monitoring backend.')
  }
}

export async function login(email, password) {
  const data = await request('/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  if (!data?.access_token) throw new ApiError('The backend did not return an access token.')
  tokenStore.set(data.access_token)
  return data
}

export async function register(username, email, password) {
  return request('/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  })
}

export const getStats = () => request('/stats')
export const getLatestEvent = () => request('/events/latest')
export const getEvents = (limit = 10) => request(`/events?limit=${limit}`)
export const getViolations = (limit = 10) => request(`/violations?limit=${limit}`)

export const uploadPrediction = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request('/predict/upload', { method: 'POST', body: formData })
}

export const getPredictionAsset = (resultUrl) => requestBlob(resultUrl)
export const getPredictionJob = (jobId) => request(`/predict/jobs/${jobId}`)
