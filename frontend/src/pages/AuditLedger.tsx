import React, { useEffect, useState } from 'react'
import { BookOpen, Shield, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { AuditLog, AuditChainVerifyResult } from '../types'
import { formatDate } from '../lib/utils'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function AuditLedger() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [verifyResult, setVerifyResult] = useState<AuditChainVerifyResult | null>(null)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    api.get('/audit/logs').then(r => setLogs(r.data)).catch(() => toast.error('Failed to load audit logs')).finally(() => setLoading(false))
  }, [])

  const verify = async () => {
    setVerifying(true)
    try {
      const { data } = await api.post('/audit/verify')
      setVerifyResult(data)
      toast[data.is_valid ? 'success' : 'error'](
        data.is_valid ? 'Audit chain verified — VALID' : 'Audit chain COMPROMISED!'
      )
    } catch { toast.error('Verification failed') }
    finally { setVerifying(false) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Audit Ledger</h1>
          <p className="text-sm text-gray-500">SHA-256 hash-chain tamper-evident audit log</p>
        </div>
        <button
          id="verify-chain-btn"
          onClick={verify}
          disabled={verifying}
          className="btn-cyber flex items-center gap-2"
        >
          <RefreshCw size={14} className={verifying ? 'animate-spin' : ''} />
          Verify Chain
        </button>
      </div>

      {/* Chain verify result */}
      {verifyResult && (
        <div className={clsx(
          'glass-card p-5 border-l-4 animate-fade-in',
          verifyResult.is_valid ? 'border-l-emerald-500/60' : 'border-l-red-500/60'
        )}>
          <div className="flex items-center gap-3 mb-2">
            {verifyResult.is_valid
              ? <CheckCircle className="w-6 h-6 text-emerald-400" />
              : <AlertCircle className="w-6 h-6 text-red-400" />
            }
            <h3 className={`text-lg font-bold ${verifyResult.is_valid ? 'text-emerald-400' : 'text-red-400'}`}>
              {verifyResult.is_valid ? '✓ AUDIT CHAIN VALID' : '✗ AUDIT CHAIN COMPROMISED'}
            </h3>
          </div>
          <p className="text-sm text-gray-300 mb-3">{verifyResult.message}</p>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div><span className="text-gray-500">Total Records</span><p className="font-mono text-gray-200">{verifyResult.total_records}</p></div>
            <div><span className="text-gray-500">Verified</span><p className="font-mono text-gray-200">{verifyResult.verified_records}</p></div>
            {verifyResult.first_broken_at && (
              <div><span className="text-gray-500">First Issue</span><p className="font-mono text-red-400">Record #{verifyResult.first_broken_at}</p></div>
            )}
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="glass-card p-4 border border-cyber-blue/10">
        <div className="flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-cyber-blue flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-gray-200 mb-1">How the Audit Chain Works</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Each audit event contains a SHA-256 hash of its own data <strong>plus</strong> the previous event's hash.
              This creates a tamper-evident chain: if any record is modified, its hash changes, which breaks the
              linkage to all subsequent records. The Verify Chain function recalculates every hash and detects any discrepancy.
            </p>
          </div>
        </div>
      </div>

      {/* Log table */}
      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading audit logs…</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Event Type</th>
                  <th>Result</th>
                  <th>Risk</th>
                  <th>Current Hash</th>
                  <th>Prev Hash</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id}>
                    <td className="mono">{log.sequence}</td>
                    <td>
                      <span className="text-xs bg-dark-600/60 border border-white/[0.06] rounded px-2 py-0.5 text-gray-300">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="text-xs text-gray-300 max-w-32 truncate">{log.result_label || '—'}</td>
                    <td className="mono">{log.risk_score != null ? log.risk_score.toFixed(0) : '—'}</td>
                    <td>
                      <span className="mono text-emerald-400 text-[10px]">
                        {log.current_hash.slice(0, 12)}…
                      </span>
                    </td>
                    <td>
                      <span className="mono text-gray-500 text-[10px]">
                        {log.previous_hash.slice(0, 12)}…
                      </span>
                    </td>
                    <td className="text-xs text-gray-500">{formatDate(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {logs.length === 0 && (
            <div className="text-center py-12 text-gray-600 text-sm">
              No audit records yet. Start by running analyses.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
