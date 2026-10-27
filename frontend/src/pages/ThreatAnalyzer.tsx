import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Search, Mail, Image, Video, Mic, Activity, Link,
  Upload, AlertCircle, CheckCircle, ChevronRight
} from 'lucide-react'
import api from '../lib/api'
import { AnalysisResult } from '../types'
import { getRiskBadgeClass, formatDate } from '../lib/utils'
import { RiskScoreDisplay, IndicatorList, XAIExplanation, ConfidenceBar } from '../components/UIComponents'
import toast from 'react-hot-toast'
import clsx from 'clsx'

type AnalysisMode = 'text' | 'url' | 'image' | 'video' | 'audio' | 'behavior'

const MODES = [
  { id: 'text', label: 'Text / Email', icon: <Mail size={18}/>, color: 'text-cyber-purple' },
  { id: 'url', label: 'URL', icon: <Link size={18}/>, color: 'text-cyber-blue' },
  { id: 'image', label: 'Image', icon: <Image size={18}/>, color: 'text-emerald-400' },
  { id: 'video', label: 'Video', icon: <Video size={18}/>, color: 'text-amber-400' },
  { id: 'audio', label: 'Audio', icon: <Mic size={18}/>, color: 'text-pink-400' },
  { id: 'behavior', label: 'Behavior', icon: <Activity size={18}/>, color: 'text-orange-400' },
] as const

const DEMO_SAMPLES = {
  text: "URGENT: Your PayPal account has been suspended due to suspicious activity. Click here immediately to verify your identity and restore access: http://paypal-secure-login.xyz/verify?token=abc123. Failure to do so within 24 hours will result in permanent account deletion.",
  url: "http://paypal-secure-login-verify.xyz/account/suspend/restore",
  behavior: { login_hour: 3, failed_attempts: 4, is_new_device: true, is_unusual_location: true, access_frequency: 25, session_duration_minutes: 5, requests_per_minute: 30 },
}

export default function ThreatAnalyzer() {
  const [mode, setMode] = useState<AnalysisMode>('text')
  const [textInput, setTextInput] = useState('')
  const [urlInput, setUrlInput] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [behavior, setBehavior] = useState({
    login_hour: 9, failed_attempts: 0, is_new_device: false,
    is_unusual_location: false, access_frequency: 5.0,
    session_duration_minutes: 45.0, requests_per_minute: 2.0,
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => setFile(files[0] || null),
    multiple: false,
    accept: mode === 'image'
      ? { 'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.webp'] }
      : mode === 'video'
      ? { 'video/*': ['.mp4', '.avi', '.mov', '.mkv'] }
      : { 'audio/*': ['.wav', '.mp3', '.ogg', '.flac'] },
  })

  const loadDemo = () => {
    if (mode === 'text') setTextInput(DEMO_SAMPLES.text)
    else if (mode === 'url') setUrlInput(DEMO_SAMPLES.url)
    else if (mode === 'behavior') setBehavior(DEMO_SAMPLES.behavior)
    toast('Demo sample loaded', { icon: '🎓' })
  }

  const analyze = async () => {
    setLoading(true)
    setResult(null)
    try {
      let res
      if (mode === 'text') {
        res = await api.post('/analyze/text', { content: textInput, content_type: 'email' })
      } else if (mode === 'url') {
        res = await api.post('/analyze/url', { url: urlInput })
      } else if (mode === 'behavior') {
        res = await api.post('/analyze/behavior', behavior)
      } else {
        if (!file) { toast.error('Please select a file'); setLoading(false); return }
        const fd = new FormData()
        fd.append('file', file)
        const endpoint = { image: '/analyze/image', video: '/analyze/video', audio: '/analyze/audio' }[mode]
        res = await api.post(endpoint!, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      }
      setResult(res.data)
      toast.success('Analysis complete')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">DarkAI Threat Analyzer</h1>
        <p className="text-sm text-gray-500">Submit content for AI-powered threat analysis</p>
      </div>

      {/* Mode selector */}
      <div className="glass-card p-4">
        <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wider">Select Analysis Type</p>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {MODES.map(m => (
            <button
              key={m.id}
              onClick={() => { setMode(m.id as AnalysisMode); setResult(null); setFile(null) }}
              className={clsx(
                'flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all text-xs font-medium',
                mode === m.id
                  ? 'border-cyber-blue/50 bg-cyber-blue/10 text-gray-100'
                  : 'border-white/[0.06] text-gray-500 hover:border-white/20 hover:text-gray-300'
              )}
            >
              <span className={mode === m.id ? m.color : ''}>{m.icon}</span>
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-200">Input</h2>
            <button onClick={loadDemo} className="btn-ghost text-xs flex items-center gap-1.5 border border-amber-500/30 text-amber-400">
              🎓 Load Demo
            </button>
          </div>

          {(mode === 'text') && (
            <textarea
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              placeholder="Paste suspicious email, SMS, or message text here…"
              className="input-cyber h-40 resize-none"
            />
          )}

          {mode === 'url' && (
            <input
              value={urlInput}
              onChange={e => setUrlInput(e.target.value)}
              placeholder="https://suspicious-site.xyz/login"
              className="input-cyber"
            />
          )}

          {(mode === 'image' || mode === 'video' || mode === 'audio') && (
            <div
              {...getRootProps()}
              className={clsx('upload-zone', isDragActive && 'upload-zone-active')}
            >
              <input {...getInputProps()} />
              <Upload className="w-8 h-8 text-gray-500 mx-auto mb-2" />
              {file ? (
                <p className="text-sm text-cyber-blue">{file.name}</p>
              ) : (
                <p className="text-sm text-gray-500">
                  Drop {mode} file here, or click to browse
                </p>
              )}
            </div>
          )}

          {mode === 'behavior' && (
            <div className="space-y-3">
              {[
                { key: 'login_hour', label: 'Login Hour (0-23)', type: 'number', min: 0, max: 23 },
                { key: 'failed_attempts', label: 'Failed Login Attempts', type: 'number', min: 0, max: 20 },
                { key: 'access_frequency', label: 'Access Frequency (/hour)', type: 'number' },
                { key: 'session_duration_minutes', label: 'Session Duration (min)', type: 'number' },
                { key: 'requests_per_minute', label: 'Requests Per Minute', type: 'number' },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-xs text-gray-400 mb-1 block">{f.label}</label>
                  <input
                    type={f.type}
                    value={(behavior as any)[f.key]}
                    onChange={e => setBehavior(b => ({ ...b, [f.key]: parseFloat(e.target.value) || 0 }))}
                    className="input-cyber"
                    min={f.min} max={f.max}
                  />
                </div>
              ))}
              <div className="flex gap-4">
                {[
                  { key: 'is_new_device', label: 'New Device' },
                  { key: 'is_unusual_location', label: 'Unusual Location' },
                ].map(f => (
                  <label key={f.key} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(behavior as any)[f.key]}
                      onChange={e => setBehavior(b => ({ ...b, [f.key]: e.target.checked }))}
                      className="w-4 h-4 rounded"
                    />
                    {f.label}
                  </label>
                ))}
              </div>
            </div>
          )}

          <button
            id="analyze-btn"
            onClick={analyze}
            disabled={loading}
            className="btn-primary w-full py-3 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Analyzing…
              </>
            ) : (
              <><Search size={16}/> Analyze</>
            )}
          </button>
        </div>

        {/* Result Panel */}
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-gray-200 mb-4">Analysis Result</h2>

          {!result && !loading && (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <Search className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-600 text-sm">Submit content to see results</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-48">
              <div className="relative w-12 h-12 mb-3">
                <div className="absolute inset-0 border-2 border-cyber-blue/30 rounded-full" />
                <div className="absolute inset-0 border-2 border-t-cyber-blue rounded-full animate-spin" />
              </div>
              <p className="text-sm text-gray-400">Running AI analysis…</p>
            </div>
          )}

          {result && (
            <div className="space-y-4 animate-fade-in">
              {/* Label */}
              <div className="flex items-center gap-2">
                {result.risk_score >= 60
                  ? <AlertCircle className="w-5 h-5 text-red-400" />
                  : <CheckCircle className="w-5 h-5 text-emerald-400" />
                }
                <span className="font-semibold text-gray-100">{result.label}</span>
                <span className={getRiskBadgeClass(result.risk_level)}>{result.risk_level}</span>
              </div>

              <RiskScoreDisplay score={result.risk_score} level={result.risk_level} />
              <ConfidenceBar value={result.confidence} label="Model Confidence" />

              <div>
                <p className="text-xs text-gray-500 mb-2">Threat Type</p>
                <span className="text-sm font-medium text-cyber-blue">
                  {result.threat_type.replace('_', ' ')} — {result.input_type}
                </span>
              </div>

              {result.indicators.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-2">Detected Indicators</p>
                  <IndicatorList indicators={result.indicators} />
                </div>
              )}

              <XAIExplanation explanation={result.explanation} />

              {result.recommended_action && (
                <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <p className="text-xs font-medium text-amber-400 mb-1">Recommended Action</p>
                  <p className="text-xs text-gray-300">{result.recommended_action}</p>
                </div>
              )}

              <p className="text-xs text-gray-600">
                Analysis ID: <span className="mono">{result.id.slice(0, 8)}…</span>
                {' • '}{formatDate(result.created_at)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
