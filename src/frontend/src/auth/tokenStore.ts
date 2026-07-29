const REFRESH_KEY = 'refresh_token'

let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setRefreshToken(token: string | null): void {
  if (token === null) {
    localStorage.removeItem(REFRESH_KEY)
  } else {
    localStorage.setItem(REFRESH_KEY, token)
  }
}

export function clearTokens(): void {
  accessToken = null
  localStorage.removeItem(REFRESH_KEY)
}

export function hasRefreshToken(): boolean {
  return Boolean(localStorage.getItem(REFRESH_KEY))
}
