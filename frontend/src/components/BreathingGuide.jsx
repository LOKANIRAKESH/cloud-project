/* eslint-disable react/prop-types */
import { useState, useEffect, useCallback } from 'react'

const PHASES = [
  { label:'Inhale', dur:4, color:'#00d9a6', instruction:'Breathe in through your nose' },
  { label:'Hold',   dur:7, color:'#7c6df5', instruction:'Hold gently' },
  { label:'Exhale', dur:8, color:'#3fb950', instruction:'Breathe out through your mouth' },
]

export default function BreathingGuide({ onClose }) {
  const [pi, setPi]         = useState(0)
  const [t, setT]           = useState(PHASES[0].dur)
  const [cycles, setCycles] = useState(0)
  const [on, setOn]         = useState(true)
  const ph = PHASES[pi]

  const tick = useCallback(() => {
    setT(prev => {
      if (prev <= 1) {
        setPi(p => { const n=(p+1)%PHASES.length; if(n===0)setCycles(c=>c+1); setT(PHASES[n].dur); return n })
        return PHASES[(pi+1)%PHASES.length].dur
      }
      return prev - 1
    })
  }, [pi])

  useEffect(() => { if (!on) return; const id=setInterval(tick,1000); return()=>clearInterval(id) }, [on,tick])

  const expanding = pi === 0 || pi === 1

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/80 backdrop-blur-sm p-4">
      <div className="bg-panel border border-border rounded-2xl p-7 max-w-xs w-full shadow-2xl flex flex-col items-center gap-5 animate-fade-up">

        <div className="flex items-center justify-between w-full">
          <div>
            <p className="text-sm font-semibold text-white">Breathing Exercise</p>
            <p className="text-[11px] text-muted font-mono">4-7-8 technique</p>
          </div>
          <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-card text-dim hover:text-muted transition-colors text-sm">✕</button>
        </div>

        {/* Circle */}
        <div className="relative w-40 h-40 flex items-center justify-center my-2">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-2 opacity-20" style={{borderColor:ph.color}}/>
          {/* Breathing circle */}
          <div
            className="absolute rounded-full border-2 flex flex-col items-center justify-center"
            style={{
              width:'100%', height:'100%',
              borderColor: ph.color,
              background: `${ph.color}12`,
              boxShadow: `0 0 20px ${ph.color}30`,
              transform: `scale(${expanding ? 1 : 0.65})`,
              transition: `transform ${ph.dur}s ease-in-out, border-color .4s, box-shadow .4s`,
            }}
          >
            <span className="font-mono text-3xl font-black" style={{color:ph.color}}>{t}</span>
            <span className="text-[9px] font-semibold uppercase tracking-widest mt-0.5" style={{color:ph.color}}>{ph.label}</span>
          </div>
        </div>

        <p className="text-xs text-muted text-center">{ph.instruction}</p>

        {/* Phase indicators */}
        <div className="flex gap-1.5">
          {PHASES.map((p,i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full transition-all"
                 style={{background: i===pi ? ph.color : '#30363d'}}/>
          ))}
        </div>

        <p className="font-mono text-[10px] text-dim">cycles: <span className="text-brand">{cycles}</span></p>

        <div className="flex gap-2 w-full">
          <button onClick={()=>setOn(o=>!o)}
            className="flex-1 py-2 text-xs font-semibold rounded-lg border border-border text-muted hover:border-brand hover:text-brand transition-colors">
            {on?'⏸ pause':'▶ resume'}
          </button>
          <button onClick={onClose}
            className="flex-1 py-2 text-xs font-semibold rounded-lg bg-brand text-bg hover:bg-branddk transition-colors">
            ✓ done
          </button>
        </div>
      </div>
    </div>
  )
}
