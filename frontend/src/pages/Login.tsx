import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Eye, EyeOff, Lock, User, AlertCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', form)
      if (data.requires_mfa) {
        // Store temp token for MFA step
        sessionStorage.setItem('darkai_temp_token', data.temp_token)
        sessionStorage.setItem('darkai_pending_user_id', data.user_id)
        sessionStorage.setItem('darkai_pending_username', data.username)
        sessionStorage.setItem('darkai_pending_role', data.role)
        navigate('/mfa')
      } else {
        // Fetch user profile
        localStorage.setItem('darkai_token', data.access_token)
        const { data: me } = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${data.access_token}` },
        })
        login(data.access_token, me)
        toast.success(`Welcome back, ${me.username}!`)
        navigate('/dashboard')
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Login failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (role: 'admin' | 'analyst' | 'user') => {
    const creds = {
      admin: { username: 'admin', password: 'Admin@1234' },
      analyst: { username: 'analyst', password: 'Analyst@1234' },
      user: { username: 'user', password: 'User@1234' },
    }
    setForm(creds[role])
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-purple/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyber-blue/10 rounded-full blur-3xl" />
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 50px, rgba(255,255,255,0.01) 50px, rgba(255,255,255,0.01) 51px), repeating-linear-gradient(90deg, transparent, transparent 50px, rgba(255,255,255,0.01) 50px, rgba(255,255,255,0.01) 51px)'
        }} />
      </div>

      <div className="w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyber-purple to-cyber-blue mb-4 shadow-lg shadow-cyber-purple/30">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gradient">DarkAI</h1>
          <p className="text-gray-500 text-sm mt-1">AI Cybersecurity Detection Platform</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          <h2 className="text-xl font-semibold text-gray-100 mb-6">Sign In</h2>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Username or Email</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  id="username"
                  type="text"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  className="input-cyber pl-9"
                  placeholder="Enter username"
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="input-cyber pl-9 pr-10"
                  placeholder="Enter password"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              id="login-btn"
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-3"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  Signing in…
                </span>
              ) : 'Sign In'}
            </button>
          </form>

          {/* Demo Mode */}
          <div className="mt-6 pt-6 border-t border-white/[0.06]">
            <p className="text-xs text-gray-500 text-center mb-3">
              🎓 <span className="text-amber-400 font-medium">DEMO MODE</span> — Quick login
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button onClick={() => fillDemo('admin')} className="btn-ghost text-xs py-1.5 border border-white/10">
                Admin
              </button>
              <button onClick={() => fillDemo('analyst')} className="btn-ghost text-xs py-1.5 border border-white/10">
                Analyst
              </button>
              <button onClick={() => fillDemo('user')} className="btn-ghost text-xs py-1.5 border border-white/10">
                User
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          B.Tech AI&ML Final Year Project — Academic Prototype
        </p>
      </div>
    </div>
  )
}
