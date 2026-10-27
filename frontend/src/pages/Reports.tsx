import React, { useEffect, useState } from 'react'
import { FileText, Download, RefreshCw } from 'lucide-react'
import api from '../lib/api'
import { Incident } from '../types'
import { getRiskBadgeClass, formatDate } from '../lib/utils'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function Reports() {
  const { isAnalyst } = useAuth()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [reportData, setReportData] = useState<any | null>(null)

  useEffect(() => {
    api.get('/incidents').then(r => setIncidents(r.data)).catch(() => toast.error('Failed to load incidents')).finally(() => setLoading(false))
  }, [])

  const generate = async (incidentId: string) => {
    setGenerating(incidentId)
    try {
      const { data } = await api.post(`/reports/generate/${incidentId}`)
      setReportData(data.report)
      toast.success(`Report generated: ${data.filename}`)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to generate report')
    } finally { setGenerating(null) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Reports</h1>
        <p className="text-sm text-gray-500">Generate security incident reports</p>
      </div>

      {reportData && (
        <div className="glass-card p-5 space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-cyber-blue">Generated Report</h2>
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url; a.download = `darkai-report-${Date.now()}.json`; a.click()
              }}
              className="btn-cyber text-xs flex items-center gap-1.5"
            >
              <Download size={12}/> Download
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div><span className="text-gray-500">Generated</span><p className="text-gray-200">{reportData.report_generated}</p></div>
            <div><span className="text-gray-500">By</span><p className="text-gray-200">{reportData.generated_by}</p></div>
            <div><span className="text-gray-500">Risk Score</span><p className="font-mono text-red-400">{reportData.incident?.risk_score}/100</p></div>
            <div><span className="text-gray-500">Risk Level</span><p className="text-red-400">{reportData.incident?.risk_level}</p></div>
          </div>
          {reportData.incident?.explanation && (
            <div className="p-3 rounded-lg bg-cyber-purple/5 border border-cyber-purple/20">
              <p className="text-xs text-cyber-purple mb-1 font-medium">XAI Explanation</p>
              <p className="text-xs text-gray-300">{reportData.incident.explanation}</p>
            </div>
          )}
          {reportData.disclaimer && (
            <p className="text-xs text-gray-600 italic">{reportData.disclaimer}</p>
          )}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading incidents…</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="data-table">
            <thead><tr>
              <th>Incident</th>
              <th>Threat Type</th>
              <th>Risk</th>
              <th>Status</th>
              <th>Created</th>
              {isAnalyst && <th>Report</th>}
            </tr></thead>
            <tbody>
              {incidents.map(inc => (
                <tr key={inc.id}>
                  <td className="text-xs max-w-48 truncate">{inc.title}</td>
                  <td className="text-xs text-gray-400">{inc.threat_type}</td>
                  <td><span className={getRiskBadgeClass(inc.risk_level)}>{Math.round(inc.risk_score)}</span></td>
                  <td className="text-xs text-gray-400">{inc.status}</td>
                  <td className="text-xs text-gray-500">{formatDate(inc.created_at)}</td>
                  {isAnalyst && (
                    <td>
                      <button
                        onClick={() => generate(inc.id)}
                        disabled={generating === inc.id}
                        className="btn-cyber text-xs flex items-center gap-1"
                      >
                        {generating === inc.id
                          ? <RefreshCw size={12} className="animate-spin" />
                          : <FileText size={12} />
                        }
                        {generating === inc.id ? 'Generating…' : 'Generate'}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          {incidents.length === 0 && (
            <div className="text-center py-12 text-gray-600 text-sm">No incidents to report</div>
          )}
        </div>
      )}
    </div>
  )
}
