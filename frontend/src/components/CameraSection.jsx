/* eslint-disable react/prop-types */
import { useEffect, useRef } from 'react'

const STATUS_MAP = {
  idle:    { cls: 'text-muted',    icon: '○' },
  ok:      { cls: 'text-lo',       icon: '●' },
  warn:    { cls: 'text-mid',      icon: '◐' },
  err:     { cls: 'text-hi',       icon: '✕' },
  loading: { cls: 'text-brand',    icon: '◌' },
}

export default function CameraSection({
  videoRef, cameraOn, scanning, analyzing, autoDetect, status,
  onStart, onStop, onAnalyze, onToggleAuto,
}) {
  const canvasRef = useRef(null)
  useEffect(() => {
    const h = () => {
      if (canvasRef.current && videoRef.current) {
        canvasRef.current.width  = videoRef.current.offsetWidth
        canvasRef.current.height = videoRef.current.offsetHeight
      }
    }
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [videoRef])

  const sm = STATUS_MAP[status.type] ?? STATUS_MAP.idle

  return (
    <section className="panel overflow-hidden">
      {/* Header — not the same as every other card */}
      <div className="px-5 pt-4 pb-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white text-sm">Live Camera</span>
          {cameraOn && <span className="flex items-center gap-1 text-[11px] text-lo font-mono"><span className="dot-live"/>LIVE</span>}
        </div>
        <div className="flex items-center gap-2">
          {/* Auto toggle — inline, compact */}
          <label className="flex items-center gap-1.5 cursor-pointer select-none">
            <span className="text-[11px] text-muted">auto</span>
            <div className="relative w-8 h-4">
              <input type="checkbox" className="sr-only peer" checked={autoDetect} disabled={!cameraOn} onChange={onToggleAuto} />
              <div className="w-full h-full rounded-full bg-card border border-border transition peer-checked:bg-brand peer-checked:border-brand peer-disabled:opacity-40"/>
              <div className="absolute top-0.5 left-0.5 w-3 h-3 bg-muted rounded-full transition peer-checked:translate-x-4 peer-checked:bg-bg"/>
            </div>
          </label>
        </div>
      </div>

      {/* Video — no margin, flush to panel */}
      <div className="relative bg-black aspect-[16/10]">
        <video
          ref={videoRef} autoPlay playsInline muted
          className={`w-full h-full object-cover [-webkit-transform:scaleX(-1)] [transform:scaleX(-1)] ${cameraOn ? '' : 'hidden'}`}
        />
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none [-webkit-transform:scaleX(-1)] [transform:scaleX(-1)]"
        />
        {scanning && <div className="scan-line" />}

        {!cameraOn && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-card/80">
            <div className="text-4xl opacity-30">📷</div>
            <p className="text-sm text-muted">Camera not started</p>
          </div>
        )}

        {/* Corner overlay — feels designed */}
        {cameraOn && (
          <div className="absolute inset-3 pointer-events-none">
            <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-brand rounded-tl" />
            <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-brand rounded-tr" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-brand rounded-bl" />
            <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-brand rounded-br" />
          </div>
        )}
      </div>

      {/* Controls — bottom bar, not card buttons */}
      <div className="px-5 py-3 border-t border-border flex items-center gap-2.5">
        <button onClick={onStart}   disabled={cameraOn}
          className="flex-1 py-2 text-xs font-semibold rounded-lg bg-brand text-bg hover:bg-branddk
                     disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
          ▶ Start
        </button>
        <button onClick={onAnalyze} disabled={!cameraOn || analyzing}
          className="flex-1 py-2 text-xs font-semibold rounded-lg border border-border text-slate-300
                     hover:border-brand hover:text-brand disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
          {analyzing ? '…scanning' : '⌕ Analyze'}
        </button>
        <button onClick={onStop}    disabled={!cameraOn}
          className="flex-1 py-2 text-xs font-semibold rounded-lg border border-hi/30 text-hi/70
                     hover:bg-hi/10 hover:text-hi disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
          ⏹ Stop
        </button>
      </div>

      {/* Status line — minimal, monospace, terminal-ish */}
      <div className={`px-5 pb-3 flex items-center gap-2 font-mono text-[11px] ${sm.cls}`}>
        <span>{sm.icon}</span>
        <span>{status.msg}</span>
        {analyzing && <span className="ml-auto text-brand animate-pulse">processing…</span>}
      </div>
    </section>
  )
}
