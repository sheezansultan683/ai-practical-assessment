import { ApiError, type ApiErrorBody } from '../types/api'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
} from '../auth/tokenStore'

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'

interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  auth?: boolean
  /** Skip the single 401 → refresh → retry cycle (used by refresh itself). */
  skipRefresh?: boolean
  /** Expect a non-JSON body (e.g. CSV download). */
  raw?: boolean
}

let refreshInFlight: Promise<boolean> | null = null
let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ApiErrorBody
    if (body?.error?.message) {
      return new ApiError(response.status, body)
    }
  } catch {
    // fall through
  }
  return new ApiError(response.status, {
    error: {
      code: 'unknown_error',
      message: `Request failed with status ${response.status}.`,
      details: null,
    },
  })
}

async function tryRefreshAccessToken(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    const refresh = getRefreshToken()
    if (!refresh) return false

    try {
      const response = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (!response.ok) {
        clearTokens()
        return false
      }
      const data = (await response.json()) as { access: string }
      setAccessToken(data.access)
      return true
    } catch {
      clearTokens()
      return false
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = 'GET',
    body,
    auth = true,
    skipRefresh = false,
    raw = false,
  } = options

  const headers: Record<string, string> = {}
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (auth) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.status === 401 && auth && !skipRefresh) {
    const refreshed = await tryRefreshAccessToken()
    if (refreshed) {
      return apiRequest<T>(path, { ...options, skipRefresh: true })
    }
    clearTokens()
    onUnauthorized?.()
    throw await parseError(response)
  }

  if (!response.ok) {
    throw await parseError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  if (raw) {
    return response as unknown as T
  }

  return (await response.json()) as T
}

export async function loginRequest(
  email: string,
  password: string,
): Promise<void> {
  const data = await apiRequest<{ access: string; refresh: string }>(
    '/api/token/',
    {
      method: 'POST',
      body: { email, password },
      auth: false,
    },
  )
  setAccessToken(data.access)
  setRefreshToken(data.refresh)
}

export async function logoutRequest(): Promise<void> {
  const refresh = getRefreshToken()
  try {
    if (refresh) {
      await apiRequest('/api/token/blacklist/', {
        method: 'POST',
        body: { refresh },
        skipRefresh: true,
      })
    }
  } catch {
    // Still clear local tokens even if blacklist fails.
  } finally {
    clearTokens()
  }
}
