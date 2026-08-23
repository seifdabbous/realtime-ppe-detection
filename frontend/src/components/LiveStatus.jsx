export default function LiveStatus({ label, connected }) {
  return (
    <div className={`status-pill ${connected ? 'is-online' : 'is-offline'}`}>
      <span className="status-dot" aria-hidden="true" />
      <span>{label}</span>
      <strong>{connected ? 'Online' : 'Offline'}</strong>
    </div>
  )
}
