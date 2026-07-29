import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import {
  apiRequest,
  loginRequest,
  logoutRequest,
  setUnauthorizedHandler,
} from '../api/client'
import { fetchMe } from '../api/tickets'
import {
  clearTokens,
  getRefreshToken,
  hasRefreshToken,
  setAccessToken,
} from './tokenStore'
import type { User } from '../types/api'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const handleUnauthorized = useCallback(() => {
    setUser(null)
    navigate('/login', { replace: true })
  }, [navigate])

  useEffect(() => {
    setUnauthorizedHandler(handleUnauthorized)
    return () => setUnauthorizedHandler(null)
  }, [handleUnauthorized])

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      if (!hasRefreshToken()) {
        if (!cancelled) {
          setLoading(false)
        }
        return
      }

      try {
        const refresh = getRefreshToken()
        if (refresh) {
          try {
            const data = await apiRequest<{ access: string }>(
              '/api/token/refresh/',
              {
                method: 'POST',
                body: { refresh },
                auth: false,
                skipRefresh: true,
              },
            )
            setAccessToken(data.access)
          } catch {
            clearTokens()
            if (!cancelled) {
              setUser(null)
              setLoading(false)
            }
            return
          }
        }
        const me = await fetchMe()
        if (!cancelled) setUser(me)
      } catch {
        clearTokens()
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    await loginRequest(email, password)
    const me = await fetchMe()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    await logoutRequest()
    setUser(null)
    navigate('/login', { replace: true })
  }, [navigate])

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
