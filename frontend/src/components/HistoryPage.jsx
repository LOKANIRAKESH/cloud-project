/* eslint-disable react/prop-types */
import { useState, useEffect, useCallback } from 'react'

const fmtTs = iso => {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('en-IN', {
      day:'2-digit', month:'short', year:'numeric',
      hour:'2-digit', minute:'2-digit', hour12:true
    })
  } catch { return iso }
}

const fmtDate = iso => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })
  } catch { return iso }
}

const LEVEL_BADGE = {
  High:     'badge-hi',
  Moderate: 'badge-mid',
  Low:      'badge-lo',
}

function path(data, W, H) {
  if (data.length < 2) return ''
  return data.map((v, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - (v / 100) * H
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

const C = s => s >= 70 ? '#f85149' : s >= 40 ? '#e3b341' : '#3fb950'

export default function HistoryPage({ authHeader }) {
  const [sessions, setSessions]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [filter, setFilter]       = useState('All')  // All | High | Moderate | Low
  const [page, setPage]           = useState(1)
  const PER_PAGE = 10

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res  = await fetch('/api/sessions', { headers: authHeader?.() ?? {} })
      const data = await res.json()
      // Newest first
      setSessions((data.sessions ?? []).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)))
    } catch { /* ignore */ } finally { setLoading(false) }
  }, [authHeader])

  useEffect(() => { load() }, [load])

  const filtered = filter === 'All' ? sessions : sessions.filter(s => s.level === filter)
  const total    = filtered.length
  const pages    = Math.max(1, Math.ceil(total / PER_PAGE))
  const visible  = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE)
  const scores   = sessions.map(s => s.score)
  const W = 600, H = 80

  const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null
  const mn  = scores.length ? Math.min(...scores) : null
  const mx  = scores.length ? Math.max(...scores) : null

  function exportCSV() {
    const rows = ['#,Timestamp,Score,Level', ...sessions.map((s, i) =>
      `${i + 1},"${fmtTs(s.timestamp)}",${s.score},${s.level}`)]
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
    Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: `stressdetect-history-${Date.now()}.csv`
    }).click()
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Session History</h2>
          <p className="text-xs text-muted mt-0.5">All your stress scans stored in DynamoDB with timestamps</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="pill hover:border-brand/50 hover:text-brand transition-colors text-xs px-3 py-1.5">
            ↻ Refresh
          </button>
          {sessions.length > 0 && (
            <button onClick={exportCSV}
              className="px-3 py-1.5 text-xs font-semibold bg-brand/10 border border-brand/30 text-brand rounded-lg hover:bg-brand/20 transition-colors">
              ↓ Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        {[
          ['Total Scans',  sessions.length, '#00d9a6'],
          ['Avg Score',    avg ?? '—',       '#6366f1'],
          ['Min Score',    mn  ?? '—',       '#3fb950'],
          ['Max Score',    mx  ?? '—',       '#f85149'],
          ['High Stress',  sessions.filter(s=>s.level==='High').length,     '#f85149'],
          ['Low Stress',   sessions.filter(s=>s.level==='Low').length,      '#3fb950'],
        ].map(([label, value, color]) => (
          <div key={label} className="stat-card">
            <div className="text-xl font-black font-mono" style={{ color }}>{value}</div>
            <div className="text-[10px] text-dim uppercase tracking-wider">{label}</div>
          </div>
        ))}
      </div>

      {/* Trend Chart */}
      {scores.length >= 2 && (
        <div className="panel p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-white uppercase tracking-widest">Stress Trend</span>
            <span className="text-[10px] text-dim font-mono">{scores.length} readings · newest first →</span>
          </div>
          <div className="bg-card rounded-xl p-3">
            <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: '80px' }}>
              <defs>
                <linearGradient id="trendGrad" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%"   stopColor="#00d9a6" stopOpacity=".2"/>
                  <stop offset="100%" stopColor="#00d9a6" stopOpacity="0"/>
                </linearGradient>
              </defs>
              {/* Reference lines */}
              {[40, 70].map(v => (
                <line key={v}
                  x1="0" y1={H - (v / 100) * H} x2={W} y2={H - (v / 100) * H}
                  stroke="#1e2d45" strokeWidth="1" strokeDasharray="4,4"/>
              ))}
              {/* Fill */}
              <path d={`${path([...scores].reverse(), W, H)} L ${W},${H} L 0,${H} Z`}
                    fill="url(#trendGrad)"/>
              {/* Line */}
              <path d={path([...scores].reverse(), W, H)}
                    fill="none" stroke="#00d9a6" strokeWidth="2"
                    strokeLinejoin="round" strokeLinecap="round"/>
              {/* Dots */}
              {[...scores].reverse().map((v, i) => {
                const x = (i / (scores.length - 1)) * W
                const y = H - (v / 100) * H
                return <circle key={i} cx={x} cy={y} r="3" fill={C(v)} stroke="#111827" strokeWidth="1.5">
                  <title>{v} — {fmtDate(sessions[sessions.length - 1 - i]?.timestamp)}</title>
                </circle>
              })}
            </svg>
            <div className="flex justify-between text-[9px] font-mono text-dim mt-1">
              <span>← oldest</span>
              <span className="text-hi">70 = high stress</span>
              <span>newest →</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter + Table */}
      <div className="panel overflow-hidden">
        {/* Filter tabs */}
        <div className="px-5 pt-4 pb-3 border-b border-border flex items-center justify-between flex-wrap gap-2">
          <div className="flex gap-1">
            {['All', 'High', 'Moderate', 'Low'].map(f => (
              <button key={f} onClick={() => { setFilter(f); setPage(1) }}
                className={`tab ${filter === f ? 'active' : ''} text-xs`}>
                {f}
              </button>
            ))}
          </div>
          <span className="font-mono text-[10px] text-dim">{total} record{total !== 1 ? 's' : ''}</span>
        </div>

        {loading ? (
          <div className="p-8 flex flex-col gap-2">
            {[1,2,3].map(i => <div key={i} className="skeleton h-10 w-full"/>)}
          </div>
        ) : total === 0 ? (
          <div className="p-12 text-center text-dim font-mono text-sm">
            {sessions.length === 0 ? '// No scans yet — run your first analysis' : '// No sessions match this filter'}
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] text-dim uppercase tracking-wider font-mono">
                    <th className="px-5 py-3 text-left">#</th>
                    <th className="px-5 py-3 text-left">Timestamp</th>
                    <th className="px-5 py-3 text-center">Score</th>
                    <th className="px-5 py-3 text-center">Level</th>
                    <th className="px-5 py-3 text-left hidden md:table-cell">Dominant Emotion</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((s, i) => {
                    const rowNum  = (page - 1) * PER_PAGE + i + 1
                    const topEmo  = s.emotions
                      ? Object.entries(s.emotions).sort((a,b)=>b[1]-a[1])[0]?.[0]
                      : null
                    return (
                      <tr key={s.timestamp ?? i}
                        className="border-b border-border/50 hover:bg-card/50 transition-colors">
                        <td className="px-5 py-3 font-mono text-dim text-xs">{rowNum}</td>
                        <td className="px-5 py-3">
                          <div className="text-xs text-slate-300">{fmtTs(s.timestamp)}</div>
                        </td>
                        <td className="px-5 py-3 text-center">
                          <span className="font-mono font-bold text-base" style={{ color: C(s.score) }}>
                            {s.score}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-center">
                          <span className={LEVEL_BADGE[s.level] ?? 'badge-neu'}>
                            {s.level}
                          </span>
                        </td>
                        <td className="px-5 py-3 hidden md:table-cell">
                          {topEmo && (
                            <span className="text-xs text-muted capitalize font-mono">{topEmo}</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pages > 1 && (
              <div className="px-5 py-3 border-t border-border flex items-center justify-between">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="text-xs text-muted hover:text-white disabled:opacity-30 transition-colors">
                  ← Prev
                </button>
                <span className="text-[11px] text-dim font-mono">Page {page} of {pages}</span>
                <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages}
                  className="text-xs text-muted hover:text-white disabled:opacity-30 transition-colors">
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
