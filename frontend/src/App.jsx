import { useCallback, useState } from 'react'
import { tokenStore } from './api/api.js'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(tokenStore.get()))
  const logout = useCallback(() => {
    tokenStore.clear()
    setAuthenticated(false)
  }, [])

  return authenticated
    ? <Dashboard onLogout={logout} />
    : <Login onAuthenticated={() => setAuthenticated(true)} />
}
