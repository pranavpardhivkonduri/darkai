import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Smartphone, AlertCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function MFAPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const refs = useRef<(HTMLInputElement | null)[]>([])

  const handleChange = (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const next = [...code]
    next[i] = val.slice(-1)
    setCode(next)
    if (val && i < 5) refs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[i] && i > 0) refs.current[i - 1]?.focus()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const totp_code = code.join('')
    if (totp_code.length !== 6) { setError('Enter the full 6-digit code'); return }
    setError('')
    setLoading(true)

    const temp_token = sessionStorage.getItem('darkai_temp_token')
    if (!temp_token) { navigate('/login'); return }

    try {
      const { data } = await api.post('/auth/mfa/verify', { temp_token, totp_code })
      localStorage.setItem('darkai_token', data.access_token)
      const { data: me } = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` }
      })
      login(data.access_token, me)
      sessionStorage.clear()
      toast.success('MFA verified! Welcome.')
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid MFA code')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyber-purple to-cyber-blue mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gradient">MFA Verification</h1>
          <p className="text-gray-500 text-sm mt-1">Enter your 6-digit TOTP code</p>
        </div>

        <div className="glass-card p-8">
          <div className="flex items-center gap-3 mb-6 p-3 rounded-lg bg-cyber-blue/5 border border-cyber-blue/20">
            <Smartphone className="w-5 h-5 text-cyber-blue" />
            <p className="text-sm text-gray-300">Open your authenticator app and enter the code</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="flex justify-center gap-2 mb-6">
              {code.map((digit, i) => (
                <input
                  key={i}
                  ref={el => refs.current[i] = el}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  className="w-10 h-12 text-center text-lg font-bold bg-dark-700 border border-white/10 rounded-lg text-cyber-blue focus:border-cyber-blue/60 focus:ring-1 focus:ring-cyber-blue/20 focus:outline-none transition-all"
                />
              ))}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? 'Verifying…' : 'Verify Code'}
            </button>
          </form>

          <button onClick={() => navigate('/login')} className="btn-ghost w-full mt-3 text-sm">
            ← Back to Login
          </button>
        </div>
      </div>
    </div>
  )
}
