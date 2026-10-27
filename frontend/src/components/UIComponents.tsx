import React from 'react'
import { getRiskBadgeClass, getRiskBarColor } from '../lib/utils'
import { RiskLevel } from '../types'

interface RiskScoreDisplayProps {
  score: number
  level: RiskLevel
  showBar?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function RiskScoreDisplay({ score, level, showBar = true, size = 'md' }: RiskScoreDisplayProps) {
  const colors = {
    LOW: 'text-emerald-400',
    MEDIUM: 'text-amber-400',
    HIGH: 'text-orange-400',
    CRITICAL: 'text-red-400',
  }
  const sizes = { sm: 'text-lg', md: 'text-2xl', lg: 'text-4xl' }

  return (
    <div>
      <div className="flex items-baseline gap-2">
        <span className={`font-bold font-mono ${sizes[size]} ${colors[level]}`}>{Math.round(score)}</span>
        <span className="text-gray-500 text-xs">/100</span>
        <span className={getRiskBadgeClass(level)}>{level}</span>
      </div>
      {showBar && (
        <div className="risk-bar-track mt-2">
          <div
            className={`h-full rounded-full transition-all duration-700 ${getRiskBarColor(score)}`}
            style={{ width: `${score}%` }}
          />
        </div>
      )}
    </div>
  )
}

interface ConfidenceBarProps {
  value: number
  label?: string
}

export function ConfidenceBar({ value, label }: ConfidenceBarProps) {
  const pct = Math.round(value * 100)
  return (
    <div>
      {label && <p className="text-xs text-gray-500 mb-1">{label}</p>}
      <div className="flex items-center gap-2">
        <div className="flex-1 risk-bar-track">
          <div
            className="h-full bg-cyber-blue rounded-full transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs font-mono text-cyber-blue w-10 text-right">{pct}%</span>
      </div>
    </div>
  )
}

interface IndicatorListProps {
  indicators: string[]
}

export function IndicatorList({ indicators }: IndicatorListProps) {
  if (!indicators.length) return <p className="text-xs text-gray-500">No specific indicators</p>
  return (
    <ul className="space-y-1.5">
      {indicators.map((ind, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
          <span className="text-red-400 mt-0.5 flex-shrink-0">⚠</span>
          {ind}
        </li>
      ))}
    </ul>
  )
}

interface XAIExplanationProps {
  explanation: string | null
}

export function XAIExplanation({ explanation }: XAIExplanationProps) {
  if (!explanation) return null
  return (
    <div className="p-4 rounded-lg bg-cyber-purple/5 border border-cyber-purple/20">
      <h4 className="text-xs font-semibold text-cyber-purple uppercase tracking-wider mb-2">
        🧠 Explainable AI — Why was this flagged?
      </h4>
      <p className="text-sm text-gray-300 leading-relaxed">{explanation}</p>
    </div>
  )
}

interface StatCardProps {
  label: string
  value: number | string
  icon: React.ReactNode
  color?: string
  sublabel?: string
}

export function StatCard({ label, value, icon, color = 'text-cyber-blue', sublabel }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 font-medium">{label}</span>
        <span className={color}>{icon}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sublabel && <p className="text-xs text-gray-600 mt-0.5">{sublabel}</p>}
    </div>
  )
}
