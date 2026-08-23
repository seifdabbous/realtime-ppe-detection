import LiveStatus from './LiveStatus.jsx'

export default function Navbar({ backendOnline, wsConnected, onLogout }) {
  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          <span />
        </div>
        <div>
          <p className="eyebrow">INDUSTRIAL VISION CONTROL</p>
          <h1>PPE Safety Monitor</h1>
        </div>
      </div>
      <div className="navbar-actions">
        <LiveStatus label="Backend" connected={backendOnline} />
        <LiveStatus label="WebSocket" connected={wsConnected} />
        <button className="logout-button" type="button" onClick={onLogout}>Sign out</button>
      </div>
    </header>
  )
}
