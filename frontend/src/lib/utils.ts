import { RiskLevel, IncidentStatus } from '../types'
import clsx from 'clsx'

export function getRiskBadgeClass(level: RiskLevel): string {
  return clsx({
    'badge-low': level === 'LOW',
    'badge-medium': level === 'MEDIUM',
    'badge-high': level === 'HIGH',
    'badge-critical': level === 'CRITICAL',
  })
}

export function getStatusBadgeClass(status: IncidentStatus): string {
  return clsx({
    'badge-open': status === 'OPEN',
    'badge-investigating': status === 'INVESTIGATING',
    'badge-resolved': status === 'RESOLVED',
    'badge-false_positive': status === 'FALSE_POSITIVE',
  })
}

export function getRiskColor(level: RiskLevel | string): string {
  switch (level) {
    case 'LOW': return '#10b981'
    case 'MEDIUM': return '#f59e0b'
    case 'HIGH': return '#f97316'
    case 'CRITICAL': return '#ef4444'
    default: return '#6b7280'
  }
}

export function getRiskBarColor(score: number): string {
  if (score < 30) return 'bg-emerald-500'
  if (score < 60) return 'bg-amber-500'
  if (score < 80) return 'bg-orange-500'
  return 'bg-red-500'
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function formatConfidence(c: number): string {
  return `${(c * 100).toFixed(1)}%`
}

export function getThreatIcon(type: string): string {
  switch (type) {
    case 'PHISHING': return '🎣'
    case 'DEEPFAKE': return '🎭'
    case 'VOICE_CLONE': return '🎙️'
    case 'ANOMALY': return '⚠️'
    case 'WATERMARK': return '🔏'
    default: return '🔍'
  }
}

export function getStatusLabel(status: IncidentStatus): string {
  switch (status) {
    case 'OPEN': return 'Open'
    case 'INVESTIGATING': return 'Investigating'
    case 'RESOLVED': return 'Resolved'
    case 'FALSE_POSITIVE': return 'False Positive'
  }
}

export function truncate(str: string, n: number = 80): string {
  return str.length > n ? str.slice(0, n) + '…' : str
}
