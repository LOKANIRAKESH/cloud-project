import { useAuth }      from './hooks/useAuth'
import LandingPage      from './components/LandingPage'
import Dashboard        from './components/Dashboard'

export default function App() {
  const { auth, isLoggedIn, login, logout } = useAuth()

  if (!isLoggedIn) {
    return <LandingPage onAuth={login}/>
  }

  return (
    <Dashboard
      user={auth}
      token={auth.access_token}
      onLogout={logout}
    />
  )
}
