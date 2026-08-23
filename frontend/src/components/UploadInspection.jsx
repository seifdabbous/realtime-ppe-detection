import { useEffect, useRef, useState } from 'react'
import { getPredictionAsset, getPredictionJob, uploadPrediction } from '../api/api.js'

const ACCEPTED = 'image/jpeg,image/png,image/webp,video/mp4,video/x-msvideo,video/quicktime,video/x-matroska,video/webm'
const MAX_SIZE = 100 * 1024 * 1024
const SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi', '.mov', '.mkv', '.webm']
const VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
const isVideoFile = (selected) => selected?.type.startsWith('video/') || VIDEO_EXTENSIONS.some((extension) => selected?.name.toLowerCase().endsWith(extension))

export default function UploadInspection() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [resultUrl, setResultUrl] = useState('')
  const [posterUrl, setPosterUrl] = useState('')
  const [result, setResult] = useState(null)
  const [mediaLoaded, setMediaLoaded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  useEffect(() => () => {
    if (resultUrl) URL.revokeObjectURL(resultUrl)
  }, [resultUrl])

  useEffect(() => () => {
    if (posterUrl) URL.revokeObjectURL(posterUrl)
  }, [posterUrl])

  const selectFile = (selected) => {
    setError('')
    setResult(null)
    if (resultUrl) URL.revokeObjectURL(resultUrl)
    setResultUrl('')
    if (posterUrl) URL.revokeObjectURL(posterUrl)
    setPosterUrl('')
    setMediaLoaded(false)
    if (!selected) return
    const extension = `.${selected.name.split('.').pop()?.toLowerCase()}`
    if (![...ACCEPTED.split(',')].includes(selected.type) && !SUPPORTED_EXTENSIONS.includes(extension)) {
      setError('Choose a supported image or video file.')
      return
    }
    if (selected.size > MAX_SIZE) {
      setError('The file must be 100 MB or smaller.')
      return
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(selected)
    setPreviewUrl(URL.createObjectURL(selected))
  }

  const runInspection = async () => {
    if (!file) return
    setLoading(true)
    setProgress(0)
    setError('')
    try {
      let prediction = await uploadPrediction(file)
      setProgress(prediction.progress || 0)
      while (prediction.status === 'queued' || prediction.status === 'processing') {
        await new Promise((resolve) => window.setTimeout(resolve, 1000))
        prediction = await getPredictionJob(prediction.job_id)
        setProgress(prediction.progress || 0)
      }
      if (prediction.status === 'failed') {
        throw new Error(prediction.error || 'Video processing failed.')
      }
      setResult(prediction)
      if (prediction.thumbnail_url) {
        const thumbnail = await getPredictionAsset(prediction.thumbnail_url)
        setPosterUrl(URL.createObjectURL(thumbnail))
      }
      const asset = await getPredictionAsset(prediction.result_url)
      if (resultUrl) URL.revokeObjectURL(resultUrl)
      setResultUrl(URL.createObjectURL(asset))
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  const violations = result?.safety_events || []

  return (
    <section className="panel upload-panel">
      <div className="panel-header">
        <div><p className="section-kicker">ON-DEMAND INSPECTION</p><h2>Analyze image or video</h2></div>
        <span className="record-count">YOLO inference</span>
      </div>

      <div className="upload-workspace">
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => { event.preventDefault(); setDragging(false); selectFile(event.dataTransfer.files[0]) }}
        >
          <input ref={inputRef} type="file" accept={ACCEPTED} onChange={(event) => selectFile(event.target.files[0])} hidden />
          {previewUrl ? (
            isVideoFile(file)
              ? <video src={previewUrl} controls muted />
              : <img src={previewUrl} alt="Selected PPE inspection" />
          ) : (
            <div className="drop-placeholder"><span className="upload-glyph">↑</span><h3>Drop safety footage here</h3><p>JPG, PNG, WEBP, MP4, AVI, MOV, MKV or WEBM · max 100 MB</p></div>
          )}
          <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()}>{file ? 'Choose another file' : 'Browse files'}</button>
        </div>

        <div className={`result-stage ${result?.safety_events_count ? 'unsafe-result' : ''}`}>
          {resultUrl ? (
            <>
              {result.kind === 'video'
                ? <video key={resultUrl} src={resultUrl} poster={posterUrl || undefined} controls autoPlay muted playsInline preload="auto" onLoadedData={() => setMediaLoaded(true)} onError={() => setError('The annotated video was created but the browser could not play it.')} />
                : <img src={resultUrl} alt="PPE detection result" onLoad={() => setMediaLoaded(true)} />}
              {!mediaLoaded && <span className="media-loading">Loading annotated result…</span>}
              <span className={`result-verdict ${result.safety_events_count ? 'unsafe' : 'safe'}`}>{result.safety_events_count ? 'Violation detected' : 'PPE compliant'}</span>
            </>
          ) : posterUrl ? (
            <><img src={posterUrl} alt="First annotated video frame" /><span className="media-loading">Loading annotated video…</span></>
          ) : (
            <div className="result-placeholder"><span>AI</span><h3>Annotated result</h3><p>Bounding boxes and PPE findings will appear here.</p></div>
          )}
        </div>
      </div>

      {file && <div className="selected-file"><span><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></span><button className="primary-button analyze-button" type="button" disabled={loading} onClick={runInspection}>{loading ? `Running AI inspection… ${progress}%` : 'Run PPE detection'}</button></div>}
      {loading && <div className="progress-track" aria-label={`Video processing ${progress}%`}><span style={{ width: `${Math.max(2, progress)}%` }} /></div>}
      {error && <div className="form-error upload-error" role="alert">{error}</div>}

      {result && (
        <div className="prediction-summary">
          <div><span>Frames analyzed</span><strong>{result.frames_processed}</strong></div>
          <div><span>Detections</span><strong>{result.detections_count}</strong></div>
          <div><span>Safety violations</span><strong className={result.safety_events_count ? 'danger-text' : ''}>{result.safety_events_count}</strong></div>
          <div><span>Finding</span><strong>{violations.length ? violations.map((item) => item.violation.replaceAll('_', ' ')).join(', ') : Object.entries(result.violation_counts || {}).map(([name, count]) => `${name.replaceAll('_', ' ')} (${count})`).join(', ') || 'CLEAR'}</strong></div>
        </div>
      )}
    </section>
  )
}
