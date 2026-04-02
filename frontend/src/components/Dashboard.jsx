/* eslint-disable react/prop-types */
import { useState, useRef, useEffect, useCallback } from 'react'
import CameraSection    from './CameraSection'
import StressGauge      from './StressGauge'
import EmotionBreakdown from './EmotionBreakdown'
import HistoryPage      from './HistoryPage'
import JournalHistoryPage from './JournalHistoryPage'

const fmtTime = () => new Date().toLocaleTimeString('en-IN', {
  hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:true
})

const TABS = [
  { id:'dashboard', icon:'⚡', label:'Dashboard' },
  { id:'history',   icon:'📊', label:'History'   },
  { id:'journal',   icon:'📝', label:'Journal'   },
]

export default function Dashboard({ user, token, onLogout }) {
  const [tab, setTab]             = useState('dashboard')
  const [cameraOn, setCameraOn]   = useState(false)
  const [scanning, setScanning]   = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [autoDetect, setAuto]     = useState(false)
  const [stressData, setStress]   = useState(null)
  const [emotions, setEmotions]   = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [history, setHistory]     = useState([])
  const [status, setStatus]       = useState({ type:'idle', msg:'Camera off' })
  const [menuOpen, setMenu]       = useState(false)
  const [sendingReport, setSendingReport] = useState(false)
  const [reportStatus, setReportStatus] = useState(null)

  const videoRef    = useRef(null)
  const streamRef   = useRef(null)
  const autoTimerRef = useRef(null)

  const authHeader = useCallback(() => ({ Authorization: `Bearer ${token}` }), [token])

  // Load history from DB on mount
  useEffect(() => {
    async function loadHistory() {
      try {
        const res  = await fetch('/api/sessions', { headers: authHeader() })
        const data = await res.json()
        const sessions = (data.sessions ?? [])
          .sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 20)
          .map(s => ({
            score: s.score,
            level: s.level,
            time:  new Date(s.timestamp).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true}),
            timestamp: s.timestamp,
          }))
        setHistory(sessions)
      } catch { /* ignore */ }
    }
    loadHistory()
  }, [authHeader])

  // ── Camera controls ──────────────────────────────────────────
  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode:'user', width:1280 } })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCameraOn(true)
      setStatus({ type:'ok', msg:'Camera active — ready to scan' })
    } catch(e) {
      setStatus({ type:'err', msg: `Camera error: ${e.message}` })
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach(t => t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    setCameraOn(false)
    setScanning(false)
    clearAutoTimer()
    setStatus({ type:'idle', msg:'Camera off' })
  }

  function clearAutoTimer() {
    if (autoTimerRef.current) { clearInterval(autoTimerRef.current); autoTimerRef.current = null }
  }

  function toggleAuto() {
    if (!cameraOn) return
    if (autoDetect) {
      clearAutoTimer()
      setAuto(false)
      setStatus({ type:'ok', msg:'Auto-detect off' })
    } else {
      setAuto(true)
      setStatus({ type:'ok', msg:'Auto-detect ON — scanning every 30s' })
      autoTimerRef.current = setInterval(analyze, 30000)
    }
  }

  // ── Capture + Analysis ───────────────────────────────────────
  async function analyze() {
    if (!cameraOn || !videoRef.current || analyzing) return
    setAnalyzing(true)
    setScanning(true)
    setStatus({ type:'loading', msg:'Analyzing with AWS Rekognition…' })

    try {
      const vid    = videoRef.current
      const canvas = document.createElement('canvas')
      canvas.width = vid.videoWidth; canvas.height = vid.videoHeight
      canvas.getContext('2d').drawImage(vid, 0, 0)
      const image  = canvas.toDataURL('image/jpeg', 0.85)

      const res    = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type':'application/json', ...authHeader() },
        body: JSON.stringify({ image }),
      })
      const data   = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Analysis failed')

      if (!data.faces_detected) {
        setStatus({ type:'warn', msg:'No face detected — ensure good lighting' })
      } else {
        const ts  = fmtTime()
        setStress(data.stress)
        setEmotions(data.emotions)
        setLastUpdate(ts)
        setHistory(h => [{
          score: data.stress.score,
          level: data.stress.level,
          time:  ts,
          timestamp: new Date().toISOString(),
        }, ...h.slice(0, 49)])
        setStatus({ type:'ok', msg:`Scan complete · ${ts}` })
        setReportStatus(null)
      }
    } catch(e) {
      setStatus({ type:'err', msg: e.message })
    } finally {
      setAnalyzing(false)
      setTimeout(() => setScanning(false), 400)
    }
  }

  // ── Send Report Email ────────────────────────────────────────
  async function sendReport() {
    if (!stressData) return
    setSendingReport(true)
    setReportStatus({ type:'loading', msg:'Sending report...' })

    try {
      const res = await fetch('/api/notifications/send-stress-alert', {
        method: 'POST',
        headers: { 'Content-Type':'application/json', ...authHeader() },
        body: JSON.stringify({
          stress_score: stressData.score,
          recommendation: getRecommendation(stressData.level),
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Failed to send report')
      
      setReportStatus({ type:'success', msg:'Report sent to your email! ✓' })
      setTimeout(() => setReportStatus(null), 3000)
    } catch(e) {
      setReportStatus({ type:'error', msg: `Error: ${e.message}` })
    } finally {
      setSendingReport(false)
    }
  }

  // ── Get Recommendation ───────────────────────────────────────
  function getRecommendation(stressLevel) {
    const recommendations = {
      'low': 'Great job managing your stress! Keep up the good work.',
      'moderate': 'Consider taking a 5-minute break or doing some light stretching.',
      'high': 'Your stress is elevated. Try deep breathing exercises or a short walk.',
      'critical': 'You\'re experiencing high stress. Please take immediate action: breathe deeply, step outside, or talk to someone.'
    }
    return recommendations[stressLevel] || 'Take care of yourself!'
  }

  useEffect(() => () => { clearAutoTimer(); stopCamera() }, [])

  const scoreColor = s => s >= 70 ? '#f85149' : s >= 40 ? '#e3b341' : '#3fb950'
  const score = stressData?.score

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      {/* ── TOP NAV ── */}
      <header className="fixed top-0 inset-x-0 z-40 border-b border-border/50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="relative">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center text-bg text-sm font-black">S</div>
              {cameraOn && <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-lo border-2 border-bg animate-blink"/>}
            </div>
            <span className="font-bold text-white text-[15px] tracking-tight hidden sm:block">
              stress<span className="text-brand">detect</span>
            </span>
          </div>

          {/* Tabs (desktop) */}
          <nav className="flex-1 flex items-center gap-1 ml-4 hidden sm:flex">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`tab flex items-center gap-1.5 ${tab === t.id ? 'active' : ''}`}>
                <span>{t.icon}</span><span>{t.label}</span>
              </button>
            ))}
          </nav>

          {/* Right: score pill + user */}
          <div className="ml-auto flex items-center gap-3">
            {score !== null && score !== undefined && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full border border-border bg-card">
                <span className="font-mono text-sm font-bold" style={{color:scoreColor(score)}}>{score}</span>
                <span className="text-[10px] text-dim">stress</span>
              </div>
            )}
            {/* User menu */}
            <div className="relative">
              <button onClick={() => setMenu(m => !m)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border hover:border-brand/30 transition-colors">
                <div className="w-6 h-6 rounded-full bg-gradient-brand flex items-center justify-center text-bg text-xs font-bold">
                  {user?.name?.[0]?.toUpperCase() ?? '?'}
                </div>
                <span className="text-xs text-muted hidden sm:block truncate max-w-[120px]">{user?.name ?? user?.email}</span>
                <span className="text-dim text-xs">{menuOpen ? '▴' : '▾'}</span>
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 w-52 glass rounded-xl border border-border shadow-card-hover z-50 overflow-hidden animate-fade-up">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-xs font-semibold text-white truncate">{user?.name}</p>
                    <p className="text-[10px] text-dim truncate">{user?.email}</p>
                  </div>
                  <button onClick={() => { setMenu(false); onLogout() }}
                    className="w-full px-4 py-2.5 text-left text-xs text-hi hover:bg-hi/10 transition-colors">
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile tab bar */}
        <div className="sm:hidden border-t border-border flex">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-1 py-2 text-xs font-medium transition-colors ${
                tab === t.id ? 'text-brand bg-brand/10' : 'text-dim'
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 pt-16 sm:pt-16 pb-8">

        {/* === DASHBOARD TAB === */}
        {tab === 'dashboard' && (
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-5">

            {/* Left column: camera */}
            <div className="lg:col-span-7 flex flex-col gap-5">
              <CameraSection
                videoRef={videoRef}
                cameraOn={cameraOn} scanning={scanning} analyzing={analyzing}
                autoDetect={autoDetect} status={status}
                onStart={startCamera} onStop={stopCamera}
                onAnalyze={analyze}   onToggleAuto={toggleAuto}
              />

              {/* Quick stats row */}
              {history.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  {[
                    ['Scans', history.length,    '#00d9a6'],
                    ['Avg',   Math.round(history.reduce((a,b)=>a+b.score,0)/history.length), '#6366f1'],
                    ['Last',  history[0]?.score, scoreColor(history[0]?.score ?? 0)],
                  ].map(([l,v,c]) => (
                    <div key={l} className="stat-card text-center">
                      <div className="text-2xl font-black font-mono" style={{color:c}}>{v ?? '—'}</div>
                      <div className="text-[10px] text-dim uppercase tracking-wider">{l}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right column: gauge + emotions + recent history */}
            <div className="lg:col-span-5 flex flex-col gap-5">
              <StressGauge stressData={stressData} lastUpdate={lastUpdate}/>
              <EmotionBreakdown emotions={
                emotions
                  ? Object.fromEntries(Object.entries(emotions).map(([k,v]) => [k, Math.round(v*100)]))
                  : null
              }/>

              {/* Send Report Button */}
              {stressData && (
                <button
                  onClick={sendReport}
                  disabled={sendingReport}
                  className="w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2
                    bg-gradient-brand text-bg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sendingReport ? (
                    <>
                      <span className="inline-block animate-spin">⚙</span>
                      Sending Report...
                    </>
                  ) : (
                    <>
                      <span>📧</span>
                      Send Report to Email
                    </>
                  )}
                </button>
              )}

              {/* Report Status Message */}
              {reportStatus && (
                <div className={`p-3 rounded-lg text-sm font-medium text-center
                  ${reportStatus.type === 'success' ? 'bg-lo/10 text-lo border border-lo/30' : 
                    reportStatus.type === 'error' ? 'bg-hi/10 text-hi border border-hi/30' : 
                    'bg-brand/10 text-brand border border-brand/30'}`}>
                  {reportStatus.msg}
                </div>
              )}

              {/* Recent sessions (mini — last 5) */}
              {history.length > 0 && (
                <div className="panel p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-white uppercase tracking-widest">Recent</span>
                    <button onClick={() => setTab('history')}
                      className="text-[11px] text-brand hover:text-branddk transition-colors font-mono">
                      View all →
                    </button>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    {history.slice(0,5).map((s,i) => (
                      <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-card">
                        <span className="font-mono font-bold text-sm w-8 text-right shrink-0"
                              style={{color:scoreColor(s.score)}}>{s.score}</span>
                        <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{width:`${s.score}%`,background:scoreColor(s.score)}}/>
                        </div>
                        <span className="font-mono text-[10px] text-dim shrink-0">{s.time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tip card */}
              <div className="panel p-4 border-brand/20"
                   style={{background:'radial-gradient(ellipse at 100% 0%, rgba(0,217,166,.06) 0%, transparent 60%)'}}>
                <div className="text-[10px] font-mono text-brand mb-1.5 uppercase tracking-widest">Tip</div>
                <p className="text-xs text-muted leading-relaxed">
                  {stressData?.advice ?? 'Turn on the camera and click Analyze to get your first stress reading.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* === HISTORY TAB === */}
        {tab === 'history' && (
          <div className="mt-6">
            <HistoryPage authHeader={authHeader}/>
          </div>
        )}

        {/* === JOURNAL TAB === */}
        {tab === 'journal' && (
          <div className="mt-6">
            <JournalHistoryPage authHeader={authHeader}/>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/30 py-3 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[10px] text-dim font-mono">
          <span>stress<span className="text-brand">detect</span> v2.1 · M-Tech Cloud ·  2026</span>
          <span className="hidden sm:block">AWS Rekognition · Azure AI Language · DynamoDB</span>
        </div>
      </footer>
    </div>
  )
}
