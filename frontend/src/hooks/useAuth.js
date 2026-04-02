/**
 * useAuth.js — Auth state hook backed by localStorage.
 * Stores JWT token + user info. Provides login/logout/authHeader helpers.
 */

import { useState, useCallback } from 'react'

const KEY = 'stressdetect_auth'

function load() {
  try { return JSON.parse(localStorage.getItem(KEY) ?? 'null') }
  catch { return null }
}

export function useAuth() {
  const [auth, setAuth] = useState(() => load())

  const login = useCallback((tokenResponse) => {
    localStorage.setItem(KEY, JSON.stringify(tokenResponse))
    setAuth(tokenResponse)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(KEY)
    setAuth(null)
  }, [])

  // Returns headers object to attach to fetch calls
  const authHeader = useCallback(() => {
    if (!auth?.access_token) return {}
    return { Authorization: `Bearer ${auth.access_token}` }
  }, [auth])

  return {
    auth,          // { access_token, user_id, name, email } | null
    isLoggedIn: !!auth,
    login,
    logout,
    authHeader,
  }
}
