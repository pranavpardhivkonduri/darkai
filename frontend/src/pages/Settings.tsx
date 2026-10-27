import React, { useState } from 'react'
import { Settings as SettingsIcon, Shield, Smartphone, Key, CheckCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import api from '../lib/api'
import toast from 'react-hot-toast'

export default function Settings() {
  const { user } = useAuth()
  const [mfaSetupData, setMfaSetupData] = useState<{ secret: string; qr_uri: string } | null>(null)
  const [totpCode, setTotpCode] = useState('')
  const [loading, setLoading] = useState(false)

  const startMfaSetup = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/auth/mfa/setup')
      setMfaSetupData(data)
    } catch { toast.error('Failed to start MFA setup') }
    finally { setLoading(false) }
  }

  const enableMfa = async () => {
    setLoading(true)
    try {
      await api.post('/auth/mfa/enable', { totp_code: totpCode })
      toast.success('MFA enabled successfully!')
      setMfaSetupData(null)
      setTotpCode('')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Invalid code')
    } finally { setLoading(false) }
  }

  const disableMfa = async () => {
    try {
      await api.post('/auth/mfa/disable')
      toast.success('MFA disabled')
    } catch { toast.error('Failed to disable MFA') }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">Account and security configuration</p>
      </div>

      {/* Profile */}
      <div className="glass-card p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
          <Shield size={15} className="text-cyber-blue" /> Profile
        </h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-gray-500 text-xs">Username</span><p className="text-gray-200">{user?.username}</p></div>
          <div><span className="text-gray-500 text-xs">Role</span><p className="text-gray-200">{user?.role}</p></div>
          <div><span className="text-gray-500 text-xs">Email</span><p className="text-gray-200">{user?.email}</p></div>
          <div><span className="text-gray-500 text-xs">Full Name</span><p className="text-gray-200">{user?.full_name || '—'}</p></div>
        </div>
      </div>

      {/* MFA */}
      <div className="glass-card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
          <Smartphone size={15} className="text-cyber-blue" /> Multi-Factor Authentication (TOTP)
        </h2>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-dark-700/50">
          {user?.mfa_enabled
            ? <CheckCircle className="w-5 h-5 text-emerald-400" />
            : <Key className="w-5 h-5 text-gray-500" />
          }
          <div>
            <p className="text-sm text-gray-200">
              MFA is currently <strong className={user?.mfa_enabled ? 'text-emerald-400' : 'text-gray-500'}>
                {user?.mfa_enabled ? 'Enabled' : 'Disabled'}
              </strong>
            </p>
            <p className="text-xs text-gray-500">Using time-based one-time passwords (TOTP)</p>
          </div>
        </div>

        {!user?.mfa_enabled && !mfaSetupData && (
          <button onClick={startMfaSetup} disabled={loading} className="btn-cyber">
            {loading ? 'Setting up…' : '+ Enable MFA'}
          </button>
        )}

        {mfaSetupData && (
          <div className="space-y-4 animate-fade-in">
            <p className="text-sm text-gray-300">
              1. Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
            </p>
            <img src={mfaSetupData.qr_uri} alt="MFA QR Code" className="w-48 h-48 rounded-lg border border-white/10" />
            <p className="text-xs text-gray-500">
              Or enter the secret manually: <span className="mono text-cyber-blue">{mfaSetupData.secret}</span>
            </p>
            <p className="text-sm text-gray-300">2. Enter the 6-digit code to confirm setup:</p>
            <input
              value={totpCode}
              onChange={e => setTotpCode(e.target.value)}
              maxLength={6}
              placeholder="000000"
              className="input-cyber w-32 text-center tracking-widest font-mono"
            />
            <button onClick={enableMfa} disabled={loading || totpCode.length !== 6} className="btn-primary">
              Confirm & Enable MFA
            </button>
          </div>
        )}

        {user?.mfa_enabled && (
          <button onClick={disableMfa} className="btn-danger text-sm">
            Disable MFA
          </button>
        )}
      </div>

      {/* Ethics */}
      <div className="glass-card p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-200">⚖️ Ethical AI Governance</h2>
        <div className="space-y-2 text-xs text-gray-400">
          {[
            ['Human Oversight', 'All detections are indicators only. Human review is required before taking enforcement actions.'],
            ['Explainability', 'Every analysis result includes an XAI explanation of why content was flagged.'],
            ['Privacy', 'Uploaded content is analyzed and stored securely. Only hashes/features, not raw content, are used in ML inference.'],
            ['False Positive Awareness', 'ML models have inherent error rates. Analysts must verify critical incidents.'],
            ['Auditability', 'All actions are logged in a tamper-evident audit chain for accountability.'],
            ['Data Minimization', 'Raw content is truncated to 1000 chars in storage. Files are only retained as needed for investigation.'],
          ].map(([title, desc]) => (
            <div key={title} className="p-3 rounded-lg bg-dark-700/40">
              <p className="font-medium text-gray-300 mb-1">{title}</p>
              <p className="text-gray-500 text-[11px]">{desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-xs text-amber-300">
          <strong>Disclaimer:</strong> DarkAI provides automated risk indicators for cybersecurity analysis.
          Results should be reviewed by qualified personnel before being treated as definitive evidence
          of malicious or criminal activity.
        </div>
      </div>
    </div>
  )
}
