import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Droplets, Upload, CheckCircle, AlertCircle, Info } from 'lucide-react'
import api from '../lib/api'
import { Watermark, WatermarkVerifyResult } from '../types'
import { formatDate } from '../lib/utils'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function WatermarkPage() {
  const [tab, setTab] = useState<'create' | 'verify'>('create')
  const [file, setFile] = useState<File | null>(null)
  const [owner, setOwner] = useState('')
  const [contentId, setContentId] = useState('')
  const [loading, setLoading] = useState(false)
  const [createResult, setCreateResult] = useState<Watermark | null>(null)
  const [verifyResult, setVerifyResult] = useState<WatermarkVerifyResult | null>(null)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: files => setFile(files[0] || null),
    multiple: false,
  })

  const handleCreate = async () => {
    if (!file || !owner || !contentId) { toast.error('Fill all fields'); return }
    setLoading(true)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('owner', owner)
    fd.append('content_id', contentId)
    try {
      const { data } = await api.post('/watermark/create', fd)
      setCreateResult(data)
      toast.success('Watermark registered')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Create failed')
    } finally { setLoading(false) }
  }

  const handleVerify = async () => {
    if (!file || !contentId) { toast.error('Provide file and content ID'); return }
    setLoading(true)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('content_id', contentId)
    try {
      const { data } = await api.post('/watermark/verify', fd)
      setVerifyResult(data)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Verification failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Digital Watermarking</h1>
        <p className="text-sm text-gray-500">Content provenance and integrity verification</p>
      </div>

      <div className="glass-card p-4 border border-cyber-blue/10 flex items-start gap-3">
        <Info className="w-5 h-5 text-cyber-blue flex-shrink-0 mt-0.5" />
        <p className="text-xs text-gray-400 leading-relaxed">
          This system uses SHA-256 hash-based content provenance — not steganographic watermarking.
          It registers the cryptographic fingerprint of content and can detect if content has been modified.
          This is not a standalone deepfake detector; it provides integrity/provenance support.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 glass-card w-fit">
        {(['create', 'verify'] as const).map(t => (
          <button
            key={t}
            onClick={() => { setTab(t); setFile(null); setCreateResult(null); setVerifyResult(null) }}
            className={clsx(
              'px-5 py-2 rounded-lg text-sm font-medium transition-all',
              tab === t ? 'bg-cyber-blue/15 text-cyber-blue border border-cyber-blue/30' : 'text-gray-400 hover:text-gray-200'
            )}
          >
            {t === 'create' ? '+ Register' : '✓ Verify'}
          </button>
        ))}
      </div>

      <div className="glass-card p-6 space-y-4">
        {/* File Drop */}
        <div {...getRootProps()} className={clsx('upload-zone', isDragActive && 'upload-zone-active')}>
          <input {...getInputProps()} />
          <Upload className="w-8 h-8 text-gray-500 mx-auto mb-2" />
          {file ? (
            <p className="text-sm text-cyber-blue">{file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
          ) : (
            <p className="text-sm text-gray-500">Drop any file here, or click to browse</p>
          )}
        </div>

        {/* Content ID */}
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Content ID (unique identifier)</label>
          <input
            value={contentId}
            onChange={e => setContentId(e.target.value)}
            placeholder="e.g. IMG-2024-001 or CONTRACT-V1"
            className="input-cyber"
          />
        </div>

        {tab === 'create' && (
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Owner / Author</label>
            <input
              value={owner}
              onChange={e => setOwner(e.target.value)}
              placeholder="e.g. John Doe"
              className="input-cyber"
            />
          </div>
        )}

        <button
          onClick={tab === 'create' ? handleCreate : handleVerify}
          disabled={loading}
          className="btn-primary w-full py-3"
        >
          {loading ? 'Processing…' : tab === 'create' ? 'Register Watermark' : 'Verify Integrity'}
        </button>
      </div>

      {/* Results */}
      {createResult && (
        <div className="glass-card p-5 border-l-4 border-l-emerald-500/50 animate-fade-in space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-emerald-400">Watermark Registered</h3>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div><span className="text-gray-500">Content ID</span><p className="mono text-gray-200">{createResult.content_id}</p></div>
            <div><span className="text-gray-500">Owner</span><p className="text-gray-200">{createResult.owner}</p></div>
            <div className="col-span-2"><span className="text-gray-500">SHA-256 Hash</span><p className="mono text-emerald-400 break-all">{createResult.content_hash}</p></div>
            <div><span className="text-gray-500">Registered</span><p className="text-gray-200">{formatDate(createResult.created_at)}</p></div>
          </div>
        </div>
      )}

      {verifyResult && (
        <div className={clsx(
          'glass-card p-5 border-l-4 animate-fade-in space-y-3',
          verifyResult.is_authentic ? 'border-l-emerald-500/60' : 'border-l-red-500/60'
        )}>
          <div className="flex items-center gap-2">
            {verifyResult.is_authentic
              ? <CheckCircle className="w-5 h-5 text-emerald-400" />
              : <AlertCircle className="w-5 h-5 text-red-400" />
            }
            <h3 className={`font-bold ${verifyResult.is_authentic ? 'text-emerald-400' : 'text-red-400'}`}>
              {verifyResult.is_authentic ? '✓ AUTHENTIC' : '✗ MODIFIED / VERIFICATION FAILED'}
            </h3>
          </div>
          <p className="text-sm text-gray-300">{verifyResult.message}</p>
          <div className="space-y-2 text-xs">
            <div><span className="text-gray-500">Computed Hash</span><p className="mono text-gray-200 break-all">{verifyResult.computed_hash}</p></div>
            {verifyResult.stored_hash && (
              <div><span className="text-gray-500">Stored Hash</span><p className={`mono break-all ${verifyResult.match ? 'text-emerald-400' : 'text-red-400'}`}>{verifyResult.stored_hash}</p></div>
            )}
            {verifyResult.owner && <div><span className="text-gray-500">Registered Owner</span><p className="text-gray-200">{verifyResult.owner}</p></div>}
          </div>
        </div>
      )}
    </div>
  )
}
