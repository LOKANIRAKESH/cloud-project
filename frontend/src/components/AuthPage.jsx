/* eslint-disable react/prop-types */
import { useState } from 'react'

export default function AuthPage({ onAuth }) {
  const [mode, setMode]     = useState('login') // 'login' | 'register'
  const [form, setForm]     = useState({ name: '', email: '', password: '' })
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body     = mode === 'login'
      ? { email: form.email, password: form.password }
      : { name: form.name, email: form.email, password: form.password }
    try {
      const res = await fetch(endpoint, {
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

  function toggle() {
    setMode(m => m === 'login' ? 'register' : 'login')
    setError(null)
  }

  const inp = `w-full bg-card border border-border rounded-xl px-4 py-2.5 text-sm text-slate-200
               placeholder-dim focus:outline-none focus:border-brand/60 focus:ring-1 focus:ring-brand/20 transition-all`

  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-4">

      {/* Brand */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-2.5 mb-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-brand flex items-center justify-center text-bg text-xl font-black">S</div>
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-hi border-2 border-bg"/>
          </div>
          <span className="font-bold text-white text-xl tracking-tight">
            stress<span className="text-brand">detect</span>
          </span>
        </div>
        <p className="text-xs text-muted font-mono">Azure AI Vision · Language · Cosmos DB</p>
      </div>

      {/* Card */}
      <div className="panel p-7 w-full max-w-sm">

        {/* Toggle */}
        <div className="flex rounded-xl bg-card border border-border p-1 mb-6">
          {['login', 'register'].map(m => (
            <button key={m} onClick={() => { setMode(m); setError(null) }}
              className={`flex-1 py-2 rounded-lg text-xs font-semibold capitalize transition-all ${
                mode === m ? 'bg-brand text-bg' : 'text-muted hover:text-slate-300'
              }`}>
              {m === 'login' ? '→ Sign In' : '+ Register'}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          {mode === 'register' && (
            <div>
              <label className="text-[11px] text-muted mb-1 block font-medium">Full Name</label>
              <input
                type="text" required value={form.name} onChange={set('name')}
                placeholder="Your name" className={inp}
              />
            </div>
          )}
          <div>
            <label className="text-[11px] text-muted mb-1 block font-medium">Email</label>
            <input
              type="email" required value={form.email} onChange={set('email')}
              placeholder="you@example.com" className={inp}
            />
          </div>
          <div>
            <label className="text-[11px] text-muted mb-1 block font-medium">Password</label>
            <input
              type="password" required value={form.password} onChange={set('password')}
              placeholder={mode === 'register' ? 'Min 6 characters' : '••••••••'} className={inp}
            />
          </div>

          {error && (
            <div className="px-3 py-2 rounded-lg bg-hi/10 border border-hi/30 text-hi font-mono text-[11px]">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="mt-1 w-full py-2.5 rounded-xl text-sm font-semibold bg-brand text-bg
                       hover:bg-branddk disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-dim">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
          <button onClick={toggle} className="text-brand hover:text-branddk transition-colors font-medium">
            {mode === 'login' ? 'Register' : 'Sign in'}
          </button>
        </p>
      </div>

      <p className="mt-6 text-[10px] text-dim font-mono">
        M-Tech Cloud Computing Project · 2026
      </p>
    </div>
  )
}
