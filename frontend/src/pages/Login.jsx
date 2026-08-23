import { useState } from 'react'
import { login, register } from '../api/api.js'

export default function Login({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'register') {
        await register(username.trim(), email.trim(), password)
      }
      await login(email.trim(), password)
      onAuthenticated()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setError('')
    setPassword('')
  }

  return (
    <main className="login-shell">
      <section className="login-context">
        <p className="eyebrow">REAL-TIME INDUSTRIAL SAFETY</p>
        <h1>Protect people.<br /><span>See risk sooner.</span></h1>
        <p>AI-powered PPE detection with live telemetry, actionable violations, and operational visibility.</p>
        <div className="login-signal"><span /><strong>Vision intelligence system</strong><small>FastAPI · Kafka · YOLO</small></div>
      </section>
      <section className="login-card">
        <div className="brand login-brand"><div className="brand-mark"><span /></div><div><p className="eyebrow">CONTROL ACCESS</p><h2>PPE Safety Monitor</h2></div></div>
        <div className="auth-tabs" role="tablist" aria-label="Account access">
          <button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>Sign in</button>
          <button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>Create account</button>
        </div>
        <div className="login-heading">
          <h3>{mode === 'login' ? 'Operator sign in' : 'Create operator account'}</h3>
          <p>{mode === 'login' ? 'Your access token is generated securely by the backend.' : 'Register once, then enter the safety dashboard immediately.'}</p>
        </div>
        <form onSubmit={submit}>
          {mode === 'register' && (
            <label>Username<input type="text" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Safety operator" minLength="1" maxLength="50" required /></label>
          )}
          <label>Email address<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="operator@company.com" required /></label>
          <label>Password<input type="password" autoComplete={mode === 'register' ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === 'register' ? 'At least 8 characters' : 'Enter your password'} minLength="8" maxLength="72" required /></label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? (mode === 'register' ? 'Creating secure account…' : 'Establishing secure session…') : (mode === 'register' ? 'Create account & continue' : 'Access dashboard')}
          </button>
        </form>
        <p className="security-note">Credentials are sent only to your configured backend. Passwords are never stored by the frontend.</p>
      </section>
    </main>
  )
}
