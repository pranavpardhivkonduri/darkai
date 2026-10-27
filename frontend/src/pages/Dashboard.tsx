import React, { useEffect, useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  Shield, AlertTriangle, Activity, Eye, Mic, Mail,
  TrendingUp, Clock, CheckCircle
} from 'lucide-react'
import api from '../lib/api'
import { DashboardStats, ThreatTimeSeries } from '../types'
import { getRiskColor, formatDate } from '../lib/utils'
import { StatCard } from '../components/UIComponents'
import toast from 'react-hot-toast'

const PIE_COLORS = ['#7c3aed', '#00d4ff', '#10b981', '#f59e0b']

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [timeline, setTimeline] = useState<ThreatTimeSeries[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [s, t] = await Promise.all([
          api.get('/dashboard/statistics'),
          api.get('/dashboard/timeline?days=7'),
        ])
        setStats(s.data)
        setTimeline(t.data)
      } catch {
        toast.error('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <Shield className="w-10 h-10 text-cyber-blue animate-pulse" />
          <p className="text-gray-400 text-sm">Loading security data…</p>
        </div>
      </div>
    )
  }

  const threatDistribution = stats ? [
    { name: 'Phishing', value: stats.phishing_detections, color: '#7c3aed' },
    { name: 'Deepfake', value: stats.deepfake_detections, color: '#00d4ff' },
    { name: 'Voice Clone', value: stats.voice_clone_detections, color: '#10b981' },
    { name: 'Anomaly', value: stats.behavioral_anomalies, color: '#f59e0b' },
  ] : []

  const riskLevelColor = getRiskColor(stats?.overall_risk_level || 'LOW')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Security Operations Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            DarkAI Threat Intelligence Platform — Real-time Analysis
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border glass-card">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-gray-400">System Active</span>
          <span className="text-xs font-mono text-gray-600">
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Overall Risk */}
      {stats && (
        <div className="glass-card p-5 border-l-4" style={{ borderLeftColor: riskLevelColor }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 mb-1">Overall System Risk Level</p>
              <div className="flex items-center gap-3">
                <span className="text-3xl font-bold" style={{ color: riskLevelColor }}>
                  {stats.overall_risk_level}
                </span>
                <span className="text-gray-500 text-sm">
                  Based on last 24 hours of threat activity
                </span>
              </div>
            </div>
            <Shield className="w-10 h-10 opacity-30" style={{ color: riskLevelColor }} />
          </div>
        </div>
      )}

      {/* Stat Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Analyses" value={stats.total_analyses} icon={<Activity size={16}/>} />
          <StatCard label="Threats Detected" value={stats.threats_detected} icon={<AlertTriangle size={16}/>} color="text-orange-400" />
          <StatCard label="Critical Incidents" value={stats.critical_incidents} icon={<Shield size={16}/>} color="text-red-400" />
          <StatCard label="Open Incidents" value={stats.open_incidents} icon={<Clock size={16}/>} color="text-amber-400" />
          <StatCard label="Phishing" value={stats.phishing_detections} icon={<Mail size={16}/>} color="text-cyber-purple" />
          <StatCard label="Deepfakes" value={stats.deepfake_detections} icon={<Eye size={16}/>} color="text-cyber-blue" />
          <StatCard label="Voice Clones" value={stats.voice_clone_detections} icon={<Mic size={16}/>} color="text-emerald-400" />
          <StatCard label="Unread Alerts" value={stats.unread_alerts} icon={<TrendingUp size={16}/>} color="text-red-400" />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="glass-card p-5 lg:col-span-2">
          <div className="section-header">
            <Activity size={16} className="text-cyber-blue" />
            <h2 className="section-title">Threats Over Time (7 Days)</h2>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="phishGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="deepGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ background: '#0a0a12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
              <Area type="monotone" dataKey="phishing" stroke="#7c3aed" fill="url(#phishGrad)" name="Phishing" strokeWidth={2} />
              <Area type="monotone" dataKey="deepfake" stroke="#00d4ff" fill="url(#deepGrad)" name="Deepfake" strokeWidth={2} />
              <Area type="monotone" dataKey="voice_clone" stroke="#10b981" fill="none" name="Voice Clone" strokeWidth={2} />
              <Area type="monotone" dataKey="anomaly" stroke="#f59e0b" fill="none" name="Anomaly" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="glass-card p-5">
          <div className="section-header">
            <AlertTriangle size={16} className="text-orange-400" />
            <h2 className="section-title">Threat Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={threatDistribution}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                dataKey="value"
                paddingAngle={3}
              >
                {threatDistribution.map((entry, idx) => (
                  <Cell key={idx} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0a0a12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {threatDistribution.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                  <span className="text-gray-400">{item.name}</span>
                </div>
                <span className="font-mono text-gray-300">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="glass-card p-4 border-l-4 border-amber-500/40">
        <p className="text-xs text-gray-500">
          <span className="text-amber-400 font-medium">⚠ Disclaimer: </span>
          DarkAI provides automated risk indicators for cybersecurity analysis. Results should be reviewed
          by qualified personnel before being treated as definitive evidence of malicious or criminal activity.
        </p>
      </div>
    </div>
  )
}
