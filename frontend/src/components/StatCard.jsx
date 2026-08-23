export default function StatCard({ label, value, tone = 'neutral', code }) {
  return (
    <article className={`stat-card tone-${tone}`}>
      <div className="stat-card-top">
        <span>{label}</span>
        <span className="stat-code">{code}</span>
      </div>
      <strong className="stat-value">{value ?? '—'}</strong>
      <div className="stat-rule" />
    </article>
  )
}
