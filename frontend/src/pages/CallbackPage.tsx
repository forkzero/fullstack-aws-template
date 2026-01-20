import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { config } from '@/lib/config'

export default function CallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const code = searchParams.get('code')
    if (code) {
      exchangeCodeForTokens(code)
    } else {
      navigate('/')
    }
  }, [searchParams, navigate])

  const exchangeCodeForTokens = async (code: string) => {
    try {
      const tokenUrl = `https://${config.cognito.domain}/oauth2/token`
      const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: config.cognito.clientId,
          code,
          redirect_uri: `${window.location.origin}/callback`,
        }),
      })

      if (response.ok) {
        const tokens = await response.json()
        localStorage.setItem('access_token', tokens.access_token)
        if (tokens.refresh_token) {
          localStorage.setItem('refresh_token', tokens.refresh_token)
        }
        navigate('/')
      } else {
        console.error('Token exchange failed')
        navigate('/')
      }
    } catch (error) {
      console.error('Token exchange error:', error)
      navigate('/')
    }
  }

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <p>Completing sign in...</p>
    </div>
  )
}
