/* eslint-disable react/prop-types */

const COLORS = {
  happiness: '#3fb950', neutral:'#8b949e', surprise:'#58a6ff',
  sadness:'#7c6df5',    fear:'#e3b341',    disgust:'#bc8cff',
  anger:'#f85149',      contempt:'#f778ba',
}

export default function EmotionBreakdown({ emotions }) {
  const sorted = emotions ? Object.entries(emotions).sort((a, b) => b[1] - a[1]) : []
  const top = sorted[0]

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold text-white uppercase tracking-widest">Emotions</span>
        {top && (
          <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-card border border-border"
                style={{ color: COLORS[top[0]] ?? '#00d9a6' }}>
            {top[0]} {top[1]}%
          </span>
        )}
      </div>

      {sorted.length === 0 ? (
        <p className="text-xs text-dim text-center py-6 font-mono">// no data</p>
      ) : (
        <div className="flex flex-col gap-2">
          {sorted.map(([name, pct]) => (
            <div key={name} className="flex items-center gap-2">
              <span className="w-20 text-[11px] text-muted capitalize shrink-0">{name}</span>
              <div className="flex-1 h-1 bg-card rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-700"
                     style={{ width:`${pct}%`, background: COLORS[name] ?? '#00d9a6' }}/>
              </div>
              <span className="font-mono text-[10px] text-dim w-8 text-right shrink-0">{pct}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
