/* eslint-disable react/prop-types */

const C = s => s>=70?'#f85149':s>=40?'#e3b341':'#3fb950'

function path(data, W, H) {
  if (data.length < 2) return ''
  return data.map((v, i) => {
    const x = (i/(data.length-1))*W
    const y = H-(v/100)*H
    return `${i===0?'M':'L'} ${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

export default function SessionHistory({ history }) {
  const scores = history.map(h=>h.score)
  const count=history.length, min=count?Math.min(...scores):null, max=count?Math.max(...scores):null
  const avg=count?Math.round(scores.reduce((a,b)=>a+b,0)/count):null
  const W=320, H=54

  function exportCSV() {
    const blob = new Blob([
      'i,time,score,level\n'+history.map((h,i)=>`${i+1},${h.time},${h.score},${h.level}`).join('\n')
    ],{type:'text/csv'})
    Object.assign(document.createElement('a'),{href:URL.createObjectURL(blob),download:`stress-${Date.now()}.csv`}).click()
  }

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-white uppercase tracking-widest">History</span>
        {count>0 && (
          <button onClick={exportCSV}
            className="font-mono text-[10px] text-muted hover:text-brand transition-colors">
            ↓ csv
          </button>
        )}
      </div>

      {/* Chart */}
      <div className="bg-card rounded-lg p-2 mb-3">
        {count < 2
          ? <div className="h-14 flex items-center justify-center font-mono text-[11px] text-dim">
              {count===0?'// awaiting readings':'// need 2+ readings'}
            </div>
          : <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{height:'54px'}}>
              <defs>
                <linearGradient id="ag" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%"   stopColor="#00d9a6" stopOpacity=".2"/>
                  <stop offset="100%" stopColor="#00d9a6" stopOpacity="0"/>
                </linearGradient>
              </defs>
              <path d={`${path(scores,W,H)} L ${W},${H} L 0,${H} Z`} fill="url(#ag)"/>
              <path d={path(scores,W,H)} fill="none" stroke="#00d9a6" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round"/>
              {scores.map((v,i)=>{
                const x=(i/(scores.length-1))*W, y=H-(v/100)*H
                return <circle key={i} cx={x} cy={y} r="2.5" fill={C(v)} stroke="#161b22" strokeWidth="1"><title>{v}</title></circle>
              })}
            </svg>
        }
      </div>

      {/* Stats — compact, monospace */}
      <div className="grid grid-cols-3 gap-2 font-mono text-center">
        {[['min',min,'#3fb950'],['avg',avg,'#00d9a6'],['max',max,'#f85149']].map(([l,v,c])=>(
          <div key={l} className="bg-card rounded-lg py-2">
            <div className="text-sm font-black" style={{color:v?c:'#484f58'}}>{v??'—'}</div>
            <div className="text-[9px] text-dim uppercase tracking-widest mt-0.5">{l}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
