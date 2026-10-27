import React, { useEffect, useState } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import api from '../lib/api'
import { Alert } from '../types'
import { getRiskBadgeClass, getThreatIcon, formatDate } from '../lib/utils'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [unreadOnly, setUnreadOnly] = useState(false)

  const load = async () => {
    try {
      const { data } = await api.get(`/alerts${unreadOnly ? '?unread_only=true' : ''}`)
      setAlerts(data)
    } catch { toast.error('Failed to load alerts') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [unreadOnly])

  const markRead = async (id: string) => {
    try {
      await api.post(`/alerts/${id}/read`)
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
    } catch { toast.error('Failed to mark as read') }
  }

  const severityBorder = {
    LOW: 'border-l-emerald-500/40',
    MEDIUM: 'border-l-amber-500/40',
    HIGH: 'border-l-orange-500/40',
    CRITICAL: 'border-l-red-500/60',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Security Alerts</h1>
          <p className="text-sm text-gray-500">System-generated threat notifications</p>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={e => setUnreadOnly(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          Unread only
        </label>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading alerts…</div>
      ) : alerts.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Bell className="w-10 h-10 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No alerts</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map(alert => (
            <div
              key={alert.id}
              className={clsx(
                'glass-card p-4 border-l-4 transition-all',
                severityBorder[alert.severity],
                !alert.is_read && 'bg-white/[0.02]'
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <span className="text-lg flex-shrink-0">{getThreatIcon(alert.alert_type)}</span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-sm text-gray-200">{alert.title}</p>
                      {!alert.is_read && (
                        <span className="w-2 h-2 rounded-full bg-cyber-blue flex-shrink-0" />
                      )}
                      <span className={getRiskBadgeClass(alert.severity)}>{alert.severity}</span>
                    </div>
                    <p className="text-xs text-gray-400">{alert.message}</p>
                    <p className="text-xs text-gray-600 mt-1">{formatDate(alert.created_at)}</p>
                  </div>
                </div>
                {!alert.is_read && (
                  <button
                    onClick={() => markRead(alert.id)}
                    className="btn-ghost text-xs flex-shrink-0 flex items-center gap-1"
                  >
                    <CheckCheck size={12} />
                    Mark read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
