import { useCallback, useEffect, useState } from 'react'
import { ApiError, getEvents, getLatestEvent, getStats, getViolations } from '../api/api.js'
import useDetectionWebSocket from '../hooks/useDetectionWebSocket.js'
import Navbar from '../components/Navbar.jsx'
import StatCard from '../components/StatCard.jsx'
import LiveEventPanel from '../components/LiveEventPanel.jsx'
import RecentViolations from '../components/RecentViolations.jsx'
import RecentEvents from '../components/RecentEvents.jsx'
import UploadInspection from '../components/UploadInspection.jsx'

const EMPTY_STATS = { total_events: null, total_violations: null, no_helmet: null, no_vest: null }

export default function Dashboard({ onLogout }) {
  const [stats, setStats] = useState(EMPTY_STATS)
  const [events, setEvents] = useState([])
  const [violations, setViolations] = useState([])
  const [latestRestEvent, setLatestRestEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [backendOnline, setBackendOnline] = useState(false)
  const [error, setError] = useState('')
  const { latestEvent, connected, error: wsError } = useDetectionWebSocket(true)

  const loadData = useCallback(async () => {
    try {
      const [statsData, eventsData, violationsData, latestData] = await Promise.all([
        getStats(), getEvents(10), getViolations(10), getLatestEvent().catch((requestError) => requestError.status === 404 ? null : Promise.reject(requestError)),
      ])
      setStats(statsData)
      setEvents(Array.isArray(eventsData) ? eventsData : [])
      setViolations(Array.isArray(violationsData) ? violationsData : [])
      setLatestRestEvent(latestData)
      setBackendOnline(true)
      setError('')
    } catch (requestError) {
      setBackendOnline(false)
      setError(requestError.message || 'Dashboard data could not be loaded.')
      if (requestError instanceof ApiError && requestError.status === 401) onLogout()
    } finally {
      setLoading(false)
    }
  }, [onLogout])

  useEffect(() => {
    loadData()
    const timer = window.setInterval(loadData, 8000)
    return () => window.clearInterval(timer)
  }, [loadData])

  return (
    <div className="app-shell">
      <Navbar backendOnline={backendOnline} wsConnected={connected} onLogout={onLogout} />
      <main className="dashboard">
        <div className="dashboard-heading">
          <div><p className="section-kicker">OPERATIONS OVERVIEW</p><h2>Safety intelligence</h2><p>Live PPE compliance across connected camera feeds.</p></div>
          <div className="refresh-note"><span>Auto refresh</span><strong>8 sec</strong></div>
        </div>
        {error && <div className="system-alert" role="alert"><strong>Backend unavailable</strong><span>{error} Retrying automatically.</span></div>}
        <section className="stats-grid" aria-label="Safety statistics">
          <StatCard label="Total Events" value={stats.total_events} code="EVT" />
          <StatCard label="Total Violations" value={stats.total_violations} code="ALT" tone="danger" />
          <StatCard label="No Helmet" value={stats.no_helmet} code="HMT" tone="warning" />
          <StatCard label="No Vest" value={stats.no_vest} code="VST" tone="warning" />
        </section>
        <UploadInspection />
        <div className="monitor-grid">
          <LiveEventPanel event={latestEvent || latestRestEvent} connected={connected} error={wsError} />
          <RecentEvents events={events} loading={loading} />
        </div>
        <RecentViolations violations={violations} loading={loading} />
      </main>
      <footer><span>PPE Safety Monitor</span><span>Real-time AI safety operations</span></footer>
    </div>
  )
}
