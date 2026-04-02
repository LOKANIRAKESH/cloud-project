/* eslint-disable react/prop-types */

export default function StressGauge({ stressData, lastUpdate }) {
  const score  = stressData?.score  ?? null
  const level  = stressData?.level  ?? null
  const advice = stressData?.advice ?? null

  const dashOffset = score !== null ? 100 - score : 100

  const scoreColorMap = { High: '#f85149', Moderate: '#e3b341', Low: '#3fb950' }
  const scoreColor = level ? (scoreColorMap[level] ?? '#00d9a6') : '#484f58'

  return (
    <div className="panel overflow-hidden">
      {/* Header row — label left, time right, different from camera header */}
      <div className="px-5 pt-4 pb-1 flex items-baseline justify-between">
        <span className="text-xs font-semibold text-white uppercase tracking-widest">Stress Score</span>
        {lastUpdate && <span className="font-mono text-[10px] text-dim">{lastUpdate}</span>}
      </div>

      {/* Gauge */}
      <div className="flex flex-col items-center pt-1 pb-2">
        <svg viewBox="0 0 200 108" className="w-48 h-24 overflow-visible">
          <defs>
            <linearGradient id="gGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#3fb950"/>
              <stop offset="55%"  stopColor="#e3b341"/>
              <stop offset="100%" stopColor="#f85149"/>
            </linearGradient>
          </defs>
          <path className="gauge-track" d="M 15 100 A 85 85 0 0 1 185 100" pathLength="100" strokeDasharray="100" strokeDashoffset="0"/>
          <path className="gauge-fill"  d="M 15 100 A 85 85 0 0 1 185 100" pathLength="100" strokeDasharray="100" strokeDashoffset={dashOffset}/>
        </svg>
        <div className="-mt-14 text-center">
          <div className="text-5xl font-black font-mono leading-none transition-all" style={{ color: scoreColor }}>
            {score !== null ? score : '--'}
          </div>
          <div className="text-[10px] font-semibold uppercase tracking-widest mt-1" style={{ color: scoreColor }}>
            {level ? `${level} Stress` : 'no scan yet'}
          </div>
        </div>
      </div>

      {/* Divider + advice — only shown when there's data */}
      {advice && (
        <div className="mx-4 mb-4 px-3 py-2.5 rounded-lg bg-card border border-border text-[11px] text-muted leading-relaxed">
          {advice}
        </div>
      )}

      {/* Scale labels — actual useful info, not decoration */}
      <div className="px-5 pb-4 flex justify-between text-[9px] font-mono uppercase text-dim tracking-widest">
        <span className="text-lo">▲ calm</span>
        <span>0 ────────────────── 100</span>
        <span className="text-hi">stressed ▲</span>
      </div>
    </div>
  )
}
