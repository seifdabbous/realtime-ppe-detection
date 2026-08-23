const formatTimestamp = (value) => value
  ? new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))
  : '—'

export default function RecentEvents({ events, loading }) {
  return (
    <section className="panel events-panel">
      <div className="panel-header">
        <div>
          <p className="section-kicker">DETECTION LOG</p>
          <h2>Recent events</h2>
        </div>
        <span className="record-count">Latest 10</span>
      </div>
      <div className="event-list">
        {events.map((event, index) => {
          const violations = event.safety_events_count ?? event.safety_events?.length ?? 0
          return (
            <article className="event-row" key={event._id || `${event.camera_id}-${event.frame_id}-${index}`}>
              <div className={`event-marker ${violations ? 'alert' : ''}`} />
              <div className="event-identity"><strong>{event.camera_id || 'Unknown camera'}</strong><span>Frame #{event.frame_id ?? '—'}</span></div>
              <div className="event-metric"><strong>{event.detections_count ?? event.detections?.length ?? 0}</strong><span>detections</span></div>
              <div className="event-metric"><strong className={violations ? 'danger-text' : ''}>{violations}</strong><span>violations</span></div>
              <time>{formatTimestamp(event.timestamp)}</time>
            </article>
          )
        })}
      </div>
      {!loading && events.length === 0 && <div className="table-empty">No detection events are available.</div>}
      {loading && events.length === 0 && <div className="table-empty">Loading detection history…</div>}
    </section>
  )
}
