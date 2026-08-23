import { useEffect, useRef, useState } from 'react'
import { tokenStore, WS_BASE_URL } from '../api/api.js'

const MAX_RECONNECT_DELAY = 10000

export default function useDetectionWebSocket(enabled = true) {
  const [latestEvent, setLatestEvent] = useState(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const reconnectAttempt = useRef(0)

  useEffect(() => {
    if (!enabled) return undefined

    let socket
    let reconnectTimer
    let stopped = false

    const connect = () => {
      const token = tokenStore.get()
      if (!token) {
        setError('A valid session is required for the live event stream.')
        return
      }

      socket = new WebSocket(`${WS_BASE_URL}/ws/events?token=${encodeURIComponent(token)}`)

      socket.onopen = () => {
        reconnectAttempt.current = 0
        setConnected(true)
        setError(null)
      }

      socket.onmessage = (message) => {
        try {
          setLatestEvent(JSON.parse(message.data))
          setError(null)
        } catch {
          setError('A malformed live event was received.')
        }
      }

      socket.onerror = () => {
        setError('Live event stream is temporarily unavailable.')
      }

      socket.onclose = (event) => {
        setConnected(false)
        if (stopped) return
        if (event.code === 1008) {
          setError('The live session was rejected. Please sign in again.')
          return
        }
        const delay = Math.min(1000 * 2 ** reconnectAttempt.current, MAX_RECONNECT_DELAY)
        reconnectAttempt.current += 1
        reconnectTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      stopped = true
      window.clearTimeout(reconnectTimer)
      if (socket && socket.readyState < WebSocket.CLOSING) socket.close()
    }
  }, [enabled])

  return { latestEvent, connected, error }
}
