import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { config } from '@/lib/config'

interface User {
  id: string
  email: string
  displayName?: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: () => void
  logout: () => void
  getAccessToken: () => string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [accessToken, setAccessToken] = useState<string | null>(null)

  useEffect(() => {
    // Check for existing session
    const storedToken = localStorage.getItem('access_token')
    if (storedToken) {
      setAccessToken(storedToken)
      fetchUserProfile(storedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchUserProfile = async (token: string) => {
    try {
      const response = await fetch('/api/users/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token invalid, clear it
        localStorage.removeItem('access_token')
        setAccessToken(null)
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const login = () => {
    // Redirect to Cognito hosted UI
    const params = new URLSearchParams({
      client_id: config.cognito.clientId,
      response_type: 'code',
      scope: 'openid email profile',
      redirect_uri: `${window.location.origin}/callback`,
    })
    window.location.href = `https://${config.cognito.domain}/oauth2/authorize?${params}`
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setAccessToken(null)
    setUser(null)

    // Redirect to Cognito logout
    const params = new URLSearchParams({
      client_id: config.cognito.clientId,
      logout_uri: window.location.origin,
    })
    window.location.href = `https://${config.cognito.domain}/logout?${params}`
  }

  const getAccessToken = () => accessToken

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      logout,
      getAccessToken,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
