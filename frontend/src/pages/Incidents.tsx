import React, { useEffect, useState } from 'react'
import { AlertTriangle, Filter, ExternalLink, ChevronDown } from 'lucide-react'
import api from '../lib/api'
import { Incident, IncidentStatus } from '../types'
import { getRiskBadgeClass, getStatusBadgeClass, getThreatIcon, formatDate, getStatusLabel } from '../lib/utils'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function Incidents() {
  const { isAnalyst } = useAuth()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Incident | null>(null)
  const [statusUpdate, setStatusUpdate] = useState('')
  const [notes, setNotes] = useState('')
  const [updating, setUpdating] = useState(false)
  const [filter, setFilter] = useState<string>('ALL')

  const load = async () => {
    try {
      const { data } = await api.get('/incidents')
      setIncidents(data)
    } catch { toast.error('Failed to load incidents') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleStatusUpdate = async () => {
    if (!selected || !statusUpdate) return
    setUpdating(true)
    try {
      await api.post(`/incidents/${selected.id}/status`, {
        status: statusUpdate,
        analyst_notes: notes || undefined,
      })
      toast.success('Incident updated')
      setSelected(null)
      setStatusUpdate('')
      setNotes('')
      load()
    } catch { toast.error('Failed to update') }
    finally { setUpdating(false) }
  }

  const filtered = filter === 'ALL' ? incidents : incidents.filter(i => i.status === filter)

  const statusColors = {
    OPEN: 'border-red-500/30',
    INVESTIGATING: 'border-amber-500/30',
    RESOLVED: 'border-emerald-500/30',
    FALSE_POSITIVE: 'border-gray-500/30',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Incident Management</h1>
          <p className="text-sm text-gray-500">Track and investigate security incidents</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-500" />
          <select
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="input-cyber w-40 text-xs"
          >
            <option value="ALL">All Status</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading incidents…</div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <AlertTriangle className="w-10 h-10 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No incidents found</p>
          <p className="text-xs text-gray-600 mt-1">Run threat analyses to generate incidents</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(inc => (
            <div
              key={inc.id}
              className={`glass-card p-4 border-l-4 ${statusColors[inc.status]} cursor-pointer hover:bg-white/[0.02] transition-all`}
              onClick={() => { setSelected(selected?.id === inc.id ? null : inc); setStatusUpdate(''); setNotes('') }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xl flex-shrink-0">{getThreatIcon(inc.threat_type)}</span>
                  <div className="min-w-0">
                    <p className="font-medium text-gray-200 text-sm truncate">{inc.title}</p>
                    <p className="text-xs text-gray-500">{formatDate(inc.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                  <span className={getRiskBadgeClass(inc.risk_level)}>{Math.round(inc.risk_score)}</span>
                  <span className={getStatusBadgeClass(inc.status)}>{getStatusLabel(inc.status)}</span>
                  <ChevronDown
                    size={14}
                    className={`text-gray-500 transition-transform ${selected?.id === inc.id ? 'rotate-180' : ''}`}
                  />
                </div>
              </div>

              {selected?.id === inc.id && (
                <div className="mt-4 pt-4 border-t border-white/[0.06] space-y-4 animate-fade-in">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div><span className="text-gray-500">Risk Score</span><p className="font-mono text-gray-200">{inc.risk_score.toFixed(1)}/100</p></div>
                    <div><span className="text-gray-500">Confidence</span><p className="font-mono text-gray-200">{(inc.confidence * 100).toFixed(1)}%</p></div>
                    <div><span className="text-gray-500">Threat Type</span><p className="text-gray-200">{inc.threat_type}</p></div>
                    <div><span className="text-gray-500">Risk Level</span><p className={getRiskBadgeClass(inc.risk_level)}>{inc.risk_level}</p></div>
                  </div>

                  {inc.explanation && (
                    <div className="p-3 rounded-lg bg-cyber-purple/5 border border-cyber-purple/20">
                      <p className="text-xs text-cyber-purple mb-1 font-medium">XAI Explanation</p>
                      <p className="text-xs text-gray-300">{inc.explanation}</p>
                    </div>
                  )}

                  {inc.analyst_notes && (
                    <div className="p-3 rounded-lg bg-dark-700/50">
                      <p className="text-xs text-gray-500 mb-1">Analyst Notes</p>
                      <p className="text-xs text-gray-300">{inc.analyst_notes}</p>
                    </div>
                  )}

                  {isAnalyst && (
                    <div className="space-y-2 pt-2 border-t border-white/[0.04]">
                      <p className="text-xs font-medium text-gray-400">Update Status</p>
                      <div className="flex gap-2">
                        <select
                          value={statusUpdate}
                          onChange={e => setStatusUpdate(e.target.value)}
                          className="input-cyber flex-1 text-xs"
                        >
                          <option value="">Select status…</option>
                          <option value="OPEN">Open</option>
                          <option value="INVESTIGATING">Investigating</option>
                          <option value="RESOLVED">Resolved</option>
                          <option value="FALSE_POSITIVE">False Positive</option>
                        </select>
                      </div>
                      <textarea
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                        placeholder="Add analyst notes…"
                        className="input-cyber text-xs h-16 resize-none"
                      />
                      <button
                        onClick={handleStatusUpdate}
                        disabled={!statusUpdate || updating}
                        className="btn-primary text-xs"
                      >
                        {updating ? 'Updating…' : 'Update Incident'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
