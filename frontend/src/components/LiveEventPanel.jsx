const formatTimestamp = (value) => value
  ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'medium' }).format(new Date(value))
  : 'Waiting for live signal'

export default function LiveEventPanel({ event, connected, error }) {
  const violations = event?.safety_events || []
  const hasViolation = (event?.safety_events_count || violations.length) > 0

  return (
    <section className={`panel live-panel ${hasViolation ? 'has-violation' : ''}`}>
      <div className="panel-header">
        <div>
          <p className="section-kicker">LIVE INFERENCE FEED</p>
          <h2>Detection telemetry</h2>
        </div>
        <span className={`live-indicator ${connected ? 'active' : ''}`}>
          <span /> {connected ? 'Receiving' : 'Standby'}
        </span>
      </div>

      {event ? (
        <>
          <div className="live-primary">
            <div>
              <span>Camera</span>
              <strong>{event.camera_id || 'Unknown'}</strong>
            </div>
            <div>
              <span>Frame</span>
              <strong>#{event.frame_id ?? '—'}</strong>
            </div>
            <div>
              <span>Detections</span>
              <strong>{event.detections_count ?? event.detections?.length ?? 0}</strong>
            </div>
            <div>
              <span>Violations</span>
              <strong className={hasViolation ? 'danger-text' : ''}>
                {event.safety_events_count ?? violations.length}
              </strong>
            </div>
          </div>
          <div className="event-footer">
            <span>{formatTimestamp(event.timestamp)}</span>
            <span className={`assessment ${hasViolation ? 'unsafe' : 'safe'}`}>
              {hasViolation ? 'Action required' : 'PPE compliant'}
            </span>
          </div>
          {hasViolation && (
            <div className="violation-strip">
              {violations.map((violation, index) => (
                <span key={`${violation.violation}-${index}`}>
                  {String(violation.violation || 'PPE violation').replaceAll('_', ' ')} · {violation.severity || 'unknown'}
                </span>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="empty-live">
          <div className="radar" aria-hidden="true"><span /></div>
          <h3>No live event received yet</h3>
          <p>{error || (connected ? 'The stream is connected and waiting for the next detection.' : 'Connecting to the live detection stream…')}</p>
        </div>
      )}
    </section>
  )
}
