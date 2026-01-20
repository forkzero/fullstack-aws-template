import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth()

  if (isLoading) {
    return <div style={{ padding: '2rem' }}>Loading...</div>
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Welcome to {{PROJECT_NAME}}</h1>

      {isAuthenticated ? (
        <div>
          <p>Logged in as: {user?.email}</p>
          <button onClick={logout} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>
            Sign Out
          </button>
        </div>
      ) : (
        <div>
          <p>Please sign in to continue.</p>
          <button onClick={login} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>
            Sign In
          </button>
        </div>
      )}
    </div>
  )
}
