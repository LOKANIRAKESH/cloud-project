/* eslint-disable react/prop-types */
import { useState, useEffect, useCallback } from 'react'

const fmtTs = iso => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day:'2-digit', month:'short', year:'numeric',
      hour:'2-digit', minute:'2-digit', hour12:true
    })
  } catch { return iso }
}

const SMETA = {
  positive: { icon:'😊', label:'Positive', cls:'badge-pos' },
  neutral:  { icon:'😐', label:'Neutral',  cls:'badge-neu' },
  mixed:    { icon:'😕', label:'Mixed',    cls:'badge-mix' },
  negative: { icon:'😟', label:'Negative', cls:'badge-neg' },
}

const MAX = 500

export default function JournalHistoryPage({ authHeader }) {
  const [entries, setEntries]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [text, setText]         = useState('')
  const [submitting, setSub]    = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)
  const [filter, setFilter]     = useState('All')

  const loadEntries = useCallback(async () => {
    setLoading(true)
    try {
      const res  = await fetch('/api/journal/history', { headers: authHeader?.() ?? {} })
      const data = await res.json()
      setEntries((data.entries ?? []).sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp)))
    } catch { /* ignore */ } finally { setLoading(false) }
  }, [authHeader])

  useEffect(() => { loadEntries() }, [loadEntries])

  async function submit(e) {
    e.preventDefault()
    if (!text.trim() || submitting) return
    setSub(true); setError(null); setResult(null)
    try {
      const res = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(authHeader?.() ?? {}) },
        body: JSON.stringify({ text: text.trim() }),
      })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.status) }
      const data = await res.json()
      setResult(data)
      setText('')
      // Reload history to show new entry
      await loadEntries()
    } catch(e) { setError(e.message) } finally { setSub(false) }
  }

  const filtered = filter === 'All' ? entries : entries.filter(e => e.sentiment === filter.toLowerCase())
  const sm = result ? (SMETA[result.sentiment] ?? SMETA.neutral) : null

  const avgStress = entries.length
    ? Math.round(entries.reduce((a,b) => a + (b.stress_score ?? 0), 0) / entries.length)
    : null

  const sentimentCounts = entries.reduce((acc, e) => {
    acc[e.sentiment] = (acc[e.sentiment] ?? 0) + 1; return acc
  }, {})

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Mood Journal</h2>
          <p className="text-xs text-muted mt-0.5">Write how you feel — Azure AI Language analyses sentiment & stress</p>
        </div>
        <span className="pill font-mono text-[10px] text-accent border-accent/30">Azure AI Language</span>
      </div>

      {/* Compose + Result */}
      <div className="panel p-5">
        <div className="text-xs font-semibold text-white uppercase tracking-widest mb-4">New Entry</div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <div className="relative">
            <textarea
              value={text}
              onChange={e => setText(e.target.value.slice(0, MAX))}
              placeholder="How are you feeling right now? Describe your mood, what's on your mind…"
              rows={4}
              className="w-full bg-card border border-border rounded-xl px-4 py-3 text-sm text-slate-300
                         placeholder-dim resize-none focus:outline-none focus:border-brand/60
                         focus:ring-1 focus:ring-brand/20 transition-all font-sans leading-relaxed"
            />
            <span className={`absolute bottom-3 right-3 font-mono text-[9px] ${text.length > MAX * .85 ? 'text-mid' : 'text-dim'}`}>
              {text.length}/{MAX}
            </span>
          </div>
          <button type="submit" disabled={!text.trim() || submitting}
            className="py-2.5 text-sm font-bold rounded-xl bg-brand text-bg hover:bg-branddk
                       disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:scale-[1.01] active:scale-[0.99]">
            {submitting ? '⏳ Analyzing…' : '⌕ Analyze Mood'}
          </button>
        </form>

        {error && (
          <div className="mt-3 px-3 py-2.5 rounded-xl bg-hi/10 border border-hi/30 text-hi text-xs font-mono">
            ⚠ {error}
          </div>
        )}

        {result && sm && (
          <div className="mt-4 flex flex-col gap-3 animate-fade-up">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-card border border-border">
              <span className="text-2xl">{sm.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={sm.cls}>{sm.label}</span>
                  <span className="text-xs text-dim font-mono">stress: {result.stress_score}</span>
                </div>
                <p className="text-xs text-muted leading-relaxed">{result.advice}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="font-mono text-2xl font-black" style={{color: sm.cls.includes('neg')?'#f85149':sm.cls.includes('pos')?'#3fb950':'#8b949e'}}>
                  {result.stress_score}
                </p>
                <p className="font-mono text-[9px] text-dim">/ 100</p>
              </div>
            </div>
            {/* Confidence bars */}
            <div className="flex flex-col gap-1.5 px-1">
              {[['positive','#3fb950'],['neutral','#8b949e'],['negative','#f85149']].map(([k,c]) => {
                const pct = Math.round((result.confidence?.[k] ?? 0) * 100)
                return (
                  <div key={k} className="flex items-center gap-3">
                    <span className="w-16 text-[10px] text-muted capitalize font-mono">{k}</span>
                    <div className="flex-1 h-1.5 bg-card rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700" style={{width:`${pct}%`,background:c}}/>
                    </div>
                    <span className="font-mono text-[10px] text-dim w-8 text-right">{pct}%</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      {entries.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            ['Total Entries',  entries.length,    '#00d9a6'],
            ['Avg Stress',     avgStress ?? '—',  '#6366f1'],
            ['Positive',       sentimentCounts.positive ?? 0, '#3fb950'],
            ['Negative',       sentimentCounts.negative ?? 0, '#f85149'],
          ].map(([label, value, color]) => (
            <div key={label} className="stat-card">
              <div className="text-2xl font-black font-mono" style={{color}}>{value}</div>
              <div className="text-[10px] text-dim uppercase tracking-wider">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* History feed */}
      <div className="panel overflow-hidden">
        <div className="px-5 pt-4 pb-3 border-b border-border flex items-center justify-between flex-wrap gap-2">
          <span className="text-xs font-semibold text-white uppercase tracking-widest">Journal History</span>
          <div className="flex gap-1">
            {['All','Positive','Neutral','Negative'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`tab text-xs ${filter === f ? 'active' : ''}`}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="p-6 flex flex-col gap-3">
            {[1,2,3].map(i => (
              <div key={i} className="flex gap-3">
                <div className="skeleton w-10 h-10 rounded-xl shrink-0"/>
                <div className="flex-1 flex flex-col gap-2">
                  <div className="skeleton h-4 w-1/3"/>
                  <div className="skeleton h-3 w-full"/>
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-dim font-mono text-sm">
            {entries.length === 0
              ? '// No journal entries yet — write your first one above'
              : '// No entries match this filter'}
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {filtered.map((entry, i) => {
              const meta = SMETA[entry.sentiment] ?? SMETA.neutral
              const scoreC = entry.stress_score >= 70 ? '#f85149' : entry.stress_score >= 40 ? '#e3b341' : '#3fb950'
              return (
                <div key={entry.timestamp ?? i}
                  className="px-5 py-4 hover:bg-card/30 transition-colors flex gap-4 items-start animate-fade-in">
                  <div className="w-10 h-10 rounded-xl bg-card border border-border flex items-center justify-center text-xl shrink-0">
                    {meta.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={meta.cls}>{meta.label}</span>
                      {entry.stress_score !== undefined && (
                        <span className="font-mono text-xs font-bold" style={{color: scoreC}}>
                          {entry.stress_score}
                        </span>
                      )}
                      <span className="font-mono text-[10px] text-dim ml-auto">{fmtTs(entry.timestamp)}</span>
                    </div>
                    <p className="text-sm text-muted leading-relaxed line-clamp-3 break-words">
                      {entry.text}
                    </p>
                    {entry.advice && (
                      <p className="text-[11px] text-dim mt-1.5 italic">{entry.advice}</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
