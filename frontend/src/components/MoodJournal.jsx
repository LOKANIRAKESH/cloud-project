/* eslint-disable react/prop-types */
import { useState } from 'react'

const SMETA = {
  positive:{ icon:'😊', label:'Positive', color:'#3fb950' },
  neutral: { icon:'😐', label:'Neutral',  color:'#8b949e' },
  mixed:   { icon:'😕', label:'Mixed',    color:'#e3b341' },
  negative:{ icon:'😟', label:'Negative', color:'#f85149' },
}

export default function MoodJournal({ authHeader }) {
  const [text, setText]       = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const [sendingReport, setSendingReport] = useState(false)
  const [reportStatus, setReportStatus] = useState(null)
  const MAX = 300

  async function submit(e) {
    e.preventDefault()
    if (!text.trim() || loading) return
    setLoading(true); setError(null); setResult(null); setReportStatus(null)
    try {
      const res = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(authHeader?.() ?? {}) },
        body: JSON.stringify({ text: text.trim() }),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || res.status) }
      setResult(await res.json())
    } catch(e) { setError(e.message) } finally { setLoading(false) }
  }

  async function sendJournalReport() {
    if (!result) return
    setSendingReport(true)
    setReportStatus({ type:'loading', msg:'Sending report...' })
    
    try {
      const res = await fetch('/api/notifications/send-journal-reminder', {
        method: 'POST',
        headers: { 'Content-Type':'application/json', ...(authHeader?.() ?? {}) },
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

  const sm = result ? (SMETA[result.sentiment]??SMETA.neutral) : null

  return (
    <div className="panel p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-white uppercase tracking-widest">Mood Journal</span>
        <span className="pill font-mono text-[10px]">Azure Language</span>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-2.5">
        <div className="relative">
          <textarea
            id="journal-input"
            value={text}
            onChange={e=>setText(e.target.value.slice(0,MAX))}
            placeholder="How are you feeling right now?"
            rows={3}
            className="w-full bg-card border border-border rounded-xl px-4 py-3 text-sm text-slate-300
                       placeholder-dim resize-none focus:outline-none focus:border-brand/60
                       focus:ring-1 focus:ring-brand/20 transition-all font-sans"
          />
          <span className={`absolute bottom-2 right-3 font-mono text-[9px] ${text.length>MAX*.9?'text-mid':'text-dim'}`}>
            {text.length}/{MAX}
          </span>
        </div>
        <button type="submit" disabled={!text.trim()||loading}
          className="py-2 text-xs font-semibold rounded-lg bg-brand text-bg hover:bg-branddk
                     disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
          {loading ? 'analyzing…' : '⌕ analyze mood'}
        </button>
      </form>

      {error && (
        <div className="px-3 py-2 rounded-lg bg-hi/10 border border-hi/30 text-hi font-mono text-[11px]">
          error: {error}
        </div>
      )}

      {result && sm && (
        <div className="flex flex-col gap-3 animate-fade-up">
          {/* Result row */}
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-card border border-border">
            <span className="text-xl">{sm.icon}</span>
            <div className="flex-1">
              <p className="text-xs font-semibold" style={{color:sm.color}}>{sm.label}</p>
              <p className="text-[11px] text-muted mt-0.5 leading-relaxed">{result.advice}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="font-mono text-lg font-black" style={{color:sm.color}}>{result.stress_score}</p>
              <p className="font-mono text-[9px] text-dim">score</p>
            </div>
          </div>

          {/* Confidence */}
          <div className="flex flex-col gap-1.5">
            {[['positive','#3fb950'],['neutral','#8b949e'],['negative','#f85149']].map(([k,c])=>{
              const pct = Math.round((result.confidence[k]??0)*100)
              return (
                <div key={k} className="flex items-center gap-2">
                  <span className="w-14 text-[10px] text-muted capitalize">{k}</span>
                  <div className="flex-1 h-1 bg-card rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{width:`${pct}%`,background:c}}/>
                  </div>
                  <span className="font-mono text-[10px] text-dim w-7 text-right">{pct}</span>
                </div>
              )
            })}
          </div>

          {/* Send Report Button */}
          <button
            onClick={sendJournalReport}
            disabled={sendingReport}
            className="w-full py-2 px-3 rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2
              bg-gradient-brand text-bg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sendingReport ? (
              <>
                <span className="inline-block animate-spin">⚙</span>
                Sending...
              </>
            ) : (
              <>
                <span>📧</span>
                Send Report to Email
              </>
            )}
          </button>

          {/* Report Status Message */}
          {reportStatus && (
            <div className={`p-2.5 rounded-lg text-xs font-medium text-center
              ${reportStatus.type === 'success' ? 'bg-lo/10 text-lo border border-lo/30' : 
                reportStatus.type === 'error' ? 'bg-hi/10 text-hi border border-hi/30' : 
                'bg-brand/10 text-brand border border-brand/30'}`}>
              {reportStatus.msg}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
