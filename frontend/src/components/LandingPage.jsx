/* eslint-disable react/prop-types */
import { useState } from 'react'
import AuthModal from './AuthModal'

const FEATURES = [
  {
    icon: '🎭',
    title: 'Real-Time Emotion Detection',
    desc: 'AWS Rekognition analyses your facial expressions live — detecting happiness, sadness, anger, fear, and more with high accuracy.',
    badge: 'AWS Rekognition',
    color: '#00d9a6',
  },
  {
    icon: '💬',
    title: 'Mood Journal Analysis',
    desc: 'Write how you feel and Azure AI Language performs deep sentiment analysis, returning stress scores and personalised advice.',
    badge: 'Azure AI Language',
    color: '#6366f1',
  },
  {
    icon: '🗄️',
    title: 'Persistent History',
    desc: 'Every scan and journal entry is saved to AWS DynamoDB with a precise timestamp — track your wellbeing over time.',
    badge: 'AWS DynamoDB',
    color: '#e3b341',
  },
  {
    icon: '📊',
    title: 'Stress Trend Analytics',
    desc: 'Visualise your stress pattern across days with interactive charts. See your min, max, and average scores at a glance.',
    badge: 'Real-time Charts',
    color: '#f85149',
  },
]

const STATS = [
  { value: 'AWS', label: 'Cloud Provider', sub: 'Rekognition + DynamoDB' },
  { value: 'Azure', label: 'AI Services', sub: 'Language + Vision' },
  { value: '<1s', label: 'Analysis Speed', sub: 'Real-time detection' },
  { value: '8', label: 'Emotions Tracked', sub: 'Per scan session' },
]

export default function LandingPage({ onAuth }) {
  const [showAuth, setShowAuth] = useState(false)
  const [authMode, setAuthMode] = useState('login')

  function openLogin()    { setAuthMode('login');    setShowAuth(true) }
  function openRegister() { setAuthMode('register'); setShowAuth(true) }

  return (
    <div className="min-h-screen bg-bg overflow-x-hidden">
      {showAuth && (
        <AuthModal
          initialMode={authMode}
          onAuth={onAuth}
          onClose={() => setShowAuth(false)}
        />
      )}

      {/* ── NAV ───────────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-40 border-b border-border/50 glass">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center text-bg text-base font-black">S</div>
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-lo border-2 border-bg animate-blink"/>
            </div>
            <span className="font-bold text-white text-[15px] tracking-tight">
              stress<span className="text-brand">detect</span>
            </span>
            <span className="hidden sm:inline font-mono text-[10px] text-dim bg-card border border-border px-1.5 py-0.5 rounded">v2.1</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={openLogin}
              className="px-4 py-1.5 text-sm text-muted hover:text-white transition-colors">
              Sign In
            </button>
            <button onClick={openRegister}
              className="px-4 py-1.5 text-sm font-semibold bg-brand text-bg rounded-lg hover:bg-branddk transition-colors">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── HERO ──────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-14 px-6">
        {/* Background glow orbs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full"
             style={{background:'radial-gradient(circle, rgba(0,217,166,.07) 0%, transparent 70%)'}}/>
        <div className="absolute top-1/3 right-1/4 w-[300px] h-[300px] rounded-full"
             style={{background:'radial-gradient(circle, rgba(99,102,241,.07) 0%, transparent 70%)'}}/>

        <div className="relative text-center max-w-3xl mx-auto animate-fade-up">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-brand/30 bg-brand/10 text-brand text-xs font-semibold mb-6">
            <span className="dot-brand"/>
            M-Tech Cloud Computing Project · 2026
          </div>

          <h1 className="text-5xl sm:text-6xl font-black tracking-tight leading-tight mb-5">
            Detect Your <span className="text-gradient">Stress</span>
            <br/>In Real Time
          </h1>

          <p className="text-lg text-muted max-w-xl mx-auto mb-8 leading-relaxed">
            AI-powered stress detection using your webcam and mood journal.
            Powered by <strong className="text-white">AWS Rekognition</strong> + <strong className="text-white">Azure AI</strong>,
            storing your history in <strong className="text-white">DynamoDB</strong>.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button onClick={openRegister}
              className="px-8 py-3.5 text-sm font-bold bg-brand text-bg rounded-xl
                         hover:bg-branddk shadow-glow-brand transition-all hover:scale-105 active:scale-95">
              🚀 Start Free — No Credit Card
            </button>
            <button onClick={openLogin}
              className="px-8 py-3.5 text-sm font-semibold border border-border rounded-xl
                         text-muted hover:border-brand/50 hover:text-white transition-all">
              → Sign In
            </button>
          </div>

          {/* Trust badges */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-8 text-[11px] text-dim font-mono">
            {['AWS Rekognition', 'Azure AI Language', 'DynamoDB', 'JWT Auth', 'End-to-End Encrypted'].map(t => (
              <span key={t} className="flex items-center gap-1">
                <span className="text-lo">✓</span> {t}
              </span>
            ))}
          </div>
        </div>

        {/* Hero visual */}
        <div className="relative mt-16 w-full max-w-2xl mx-auto animate-fade-up" style={{animationDelay:'.15s'}}>
          <div className="glass rounded-2xl overflow-hidden shadow-card-hover">
            {/* Fake app preview */}
            <div className="bg-panel/80 px-4 py-2.5 border-b border-border flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-hi"/>
                <div className="w-3 h-3 rounded-full bg-mid"/>
                <div className="w-3 h-3 rounded-full bg-lo"/>
              </div>
              <div className="flex-1 mx-4 h-5 bg-card rounded text-[10px] text-dim flex items-center px-2 font-mono">
                stressdetect.app/dashboard
              </div>
            </div>
            <div className="p-5 grid grid-cols-3 gap-3">
              {/* Fake camera feed */}
              <div className="col-span-2 bg-black rounded-xl overflow-hidden aspect-video flex items-center justify-center relative">
                <div className="text-4xl opacity-20">📷</div>
                <div className="scan-line absolute top-1/2"/>
                <div className="absolute inset-3">
                  <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-brand rounded-tl"/>
                  <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-brand rounded-tr"/>
                  <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-brand rounded-bl"/>
                  <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-brand rounded-br"/>
                </div>
                <div className="absolute top-2 left-2 flex items-center gap-1 text-[10px] text-lo font-mono bg-black/50 px-2 py-0.5 rounded">
                  <span className="dot-live"/>LIVE
                </div>
              </div>
              {/* Fake gauge */}
              <div className="bg-card rounded-xl p-3 flex flex-col items-center justify-center gap-2">
                <div className="text-[10px] text-dim font-mono uppercase tracking-widest">Stress Score</div>
                <div className="text-4xl font-black font-mono text-lo">32</div>
                <div className="text-[10px] font-semibold text-lo">Low Stress</div>
                <div className="w-full h-1 bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-lo rounded-full" style={{width:'32%'}}/>
                </div>
              </div>
              {/* Emotion bars */}
              <div className="col-span-3 bg-card rounded-xl p-3">
                <div className="text-[10px] text-dim font-mono mb-2">Emotion Breakdown</div>
                <div className="flex gap-2">
                  {[['Happiness','#3fb950',78],['Calm','#8b949e',15],['Surprise','#58a6ff',7]].map(([n,c,v])=>(
                    <div key={n} className="flex-1">
                      <div className="h-1 bg-border rounded-full overflow-hidden mb-1">
                        <div className="h-full rounded-full transition-all" style={{width:`${v}%`,background:c}}/>
                      </div>
                      <div className="text-[9px] font-mono" style={{color:c}}>{n} {v}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          {/* Glow under the card */}
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-2/3 h-16 rounded-full blur-2xl"
               style={{background:'rgba(0,217,166,.15)'}}/>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-dim text-xs font-mono animate-float flex flex-col items-center gap-1">
          <span>scroll to explore</span>
          <span className="text-lg">↓</span>
        </div>
      </section>

      {/* ── STATS ─────────────────────────────────────────────── */}
      <section className="py-16 px-6 border-y border-border/50">
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6">
          {STATS.map(({ value, label, sub }) => (
            <div key={label} className="text-center">
              <div className="text-3xl font-black text-gradient mb-1">{value}</div>
              <div className="text-sm font-semibold text-white">{label}</div>
              <div className="text-[11px] text-dim mt-0.5">{sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ──────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-black text-white mb-3">Everything You Need</h2>
            <p className="text-muted max-w-lg mx-auto">
              Built on enterprise cloud infrastructure — research-grade AI, zero setup.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {FEATURES.map(({ icon, title, desc, badge, color }) => (
              <div key={title}
                className="panel p-6 hover:border-brand/30 transition-all duration-300 hover:shadow-card-hover group">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                       style={{background: `${color}15`, border: `1px solid ${color}25`}}>
                    {icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1.5">
                      <h3 className="font-bold text-white text-sm">{title}</h3>
                    </div>
                    <p className="text-muted text-sm leading-relaxed mb-3">{desc}</p>
                    <span className="pill text-[10px] font-mono" style={{color, borderColor: `${color}30`}}>
                      {badge}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────────── */}
      <section className="py-20 px-6 border-t border-border/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-black text-white mb-3">How It Works</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              { step:'01', icon:'📷', title:'Turn On Camera', desc:'Grant camera access. Your stream stays local — only a JPEG frame is sent for analysis.' },
              { step:'02', icon:'🧠', title:'AI Analyses You', desc:'AWS Rekognition detects emotions. Azure Language analyses your journal text.' },
              { step:'03', icon:'📊', title:'Track Over Time', desc:'Every reading is saved to DynamoDB with a timestamp. View trends, export CSV.' },
            ].map(({step,icon,title,desc}) => (
              <div key={step} className="relative panel p-6 text-center">
                <div className="text-3xl mb-3">{icon}</div>
                <div className="font-mono text-[11px] text-brand mb-1">{step}</div>
                <h3 className="font-bold text-white mb-2">{title}</h3>
                <p className="text-sm text-muted leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="py-20 px-6 border-t border-border/50">
        <div className="max-w-2xl mx-auto text-center">
          <div className="panel p-10" style={{background:'radial-gradient(ellipse at 50% 0%, rgba(0,217,166,.08) 0%, transparent 70%)'}}>
            <div className="text-4xl mb-4">🧘</div>
            <h2 className="text-3xl font-black text-white mb-3">
              Start Managing Your Stress Today
            </h2>
            <p className="text-muted mb-7">
              Free to use. No credit card. Real AI. Real insights.
            </p>
            <button onClick={openRegister}
              className="px-10 py-3.5 text-sm font-bold bg-brand text-bg rounded-xl
                         hover:bg-branddk shadow-glow-brand transition-all hover:scale-105 active:scale-95">
              Create Free Account →
            </button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────── */}
      <footer className="border-t border-border/50 py-6 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-dim font-mono">
          <span>stress<span className="text-brand">detect</span> · M-Tech Cloud Computing · 2026</span>
          <span>AWS Rekognition · Azure AI Language · DynamoDB · FastAPI · React</span>
        </div>
      </footer>
    </div>
  )
}
