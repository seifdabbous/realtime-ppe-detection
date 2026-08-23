const formatTimestamp = (value) => value
  ? new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))
  : '—'

export default function RecentViolations({ violations, loading }) {
  return (
    <section className="panel table-panel">
      <div className="panel-header">
        <div>
          <p className="section-kicker">SAFETY EXCEPTIONS</p>
          <h2>Recent violations</h2>
        </div>
        <span className="record-count">{violations.length} records</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Camera</th><th>Frame</th><th>Violation</th><th>Severity</th><th>Confidence</th><th>Timestamp</th></tr></thead>
          <tbody>
            {violations.map((item, index) => (
              <tr key={item.event_id ? `${item.event_id}-${index}` : `${item.camera_id}-${item.frame_id}-${index}`}>
                <td><span className="camera-cell">{item.camera_id || '—'}</span></td>
                <td>#{item.frame_id ?? '—'}</td>
                <td>{String(item.violation || 'Unknown').replaceAll('_', ' ')}</td>
                <td><span className={`severity-badge severity-${String(item.severity || 'low').toLowerCase()}`}>{item.severity || 'low'}</span></td>
                <td>{typeof item.confidence === 'number' ? `${(item.confidence * 100).toFixed(1)}%` : '—'}</td>
                <td className="timestamp-cell">{formatTimestamp(item.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!loading && violations.length === 0 && <div className="table-empty">No PPE violations have been recorded.</div>}
      {loading && violations.length === 0 && <div className="table-empty">Loading safety history…</div>}
    </section>
  )
}
