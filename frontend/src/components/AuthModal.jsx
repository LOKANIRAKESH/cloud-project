/* eslint-disable react/prop-types */
import { useState, useEffect } from 'react'

export default function AuthModal({ initialMode = 'login', onAuth, onClose }) {
  const [mode, setMode]     = useState(initialMode)
  const [form, setForm]     = useState({ name: '', email: '', password: '' })
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  // close on Escape
  useEffect(() => {
    const h = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body     = mode === 'login'
      ? { email: form.email, password: form.password }
      : { name: form.name, email: form.email, password: form.password }
    try {
      const res  = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      onAuth(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function toggle() { setMode(m => m === 'login' ? 'register' : 'login'); setError(null) }

  const inp = `w-full bg-card border border-border rounded-xl px-4 py-3 text-sm text-slate-200
               placeholder-dim focus:outline-none focus:border-brand/60 focus:ring-1
               focus:ring-brand/20 transition-all`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         onClick={e => e.target === e.currentTarget && onClose()}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-bg/80 backdrop-blur-sm animate-fade-in"/>

      {/* Modal */}
      <div className="relative w-full max-w-md animate-fade-up">
        <div className="glass rounded-2xl p-8 shadow-card-hover">
          {/* Close */}
          <button onClick={onClose}
            className="absolute top-4 right-4 text-dim hover:text-white transition-colors text-lg">✕</button>

          {/* Brand */}
          <div className="text-center mb-7">
            <div className="inline-flex items-center gap-2.5 mb-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center text-bg text-xl font-black">S</div>
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-lo border-2 border-bg"/>
              </div>
              <span className="font-bold text-white text-xl tracking-tight">
                stress<span className="text-brand">detect</span>
              </span>
            </div>
            <p className="text-xs text-dim font-mono">
              {mode === 'login' ? 'Welcome back' : 'Create your free account'}
            </p>
          </div>

          {/* Toggle */}
          <div className="flex rounded-xl bg-card border border-border p-1 mb-6">
            {['login', 'register'].map(m => (
              <button key={m} onClick={() => { setMode(m); setError(null) }}
                className={`flex-1 py-2.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                  mode === m ? 'bg-brand text-bg shadow-glow-brand' : 'text-muted hover:text-slate-300'
                }`}>
                {m === 'login' ? '→ Sign In' : '＋ Register'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="flex flex-col gap-4">
            {mode === 'register' && (
              <div>
                <label className="text-[11px] text-muted mb-1.5 block font-medium tracking-wide">Full Name</label>
                <input type="text" required value={form.name} onChange={set('name')}
                  placeholder="Your name" className={inp}/>
              </div>
            )}
            <div>
              <label className="text-[11px] text-muted mb-1.5 block font-medium tracking-wide">Email Address</label>
              <input type="email" required value={form.email} onChange={set('email')}
                placeholder="you@example.com" className={inp}/>
            </div>
            <div>
              <label className="text-[11px] text-muted mb-1.5 block font-medium tracking-wide">Password</label>
              <input type="password" required value={form.password} onChange={set('password')}
                placeholder={mode === 'register' ? 'Min 6 characters' : '••••••••'} className={inp}/>
            </div>

            {error && (
              <div className="px-3 py-2.5 rounded-xl bg-hi/10 border border-hi/30 text-hi text-xs font-mono">
                ⚠ {error}
              </div>
            )}

            <button type="submit" disabled={loading}
              className="mt-1 w-full py-3.5 rounded-xl text-sm font-bold bg-brand text-bg
                         hover:bg-branddk shadow-glow-brand disabled:opacity-40 disabled:cursor-not-allowed
                         transition-all hover:scale-[1.02] active:scale-[0.98]">
              {loading ? '⏳ Please wait…' : mode === 'login' ? '→ Sign In' : '🚀 Create Account'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-dim">
            {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button onClick={toggle} className="text-brand hover:text-branddk transition-colors font-medium">
              {mode === 'login' ? 'Register free' : 'Sign in'}
            </button>
          </p>

          <p className="mt-4 text-center text-[10px] text-dim font-mono">
            M-Tech Cloud Computing · 2026
          </p>
        </div>
      </div>
    </div>
  )
}
