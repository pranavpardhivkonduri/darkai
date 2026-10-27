// ─── Auth ───────────────────────────────────────────────────
export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  role: 'ADMIN' | 'ANALYST' | 'USER'
  is_active: boolean
  mfa_enabled: boolean
  failed_login_attempts: number
  last_login: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  requires_mfa: boolean
  temp_token?: string
  user_id: string
  username: string
  role: string
}

// ─── Analysis ───────────────────────────────────────────────
export type ThreatType = 'DEEPFAKE' | 'VOICE_CLONE' | 'PHISHING' | 'ANOMALY' | 'WATERMARK' | 'UNKNOWN'
export type InputType = 'IMAGE' | 'VIDEO' | 'AUDIO' | 'TEXT' | 'URL' | 'BEHAVIOR'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE'

export interface AnalysisResult {
  id: string
  user_id: string
  input_type: InputType
  threat_type: ThreatType
  filename: string | null
  raw_input: string | null
  label: string
  confidence: number
  risk_score: number
  risk_level: RiskLevel
  indicators: string[]
  explanation: string | null
  recommended_action: string | null
  model_features: Record<string, unknown>
  created_at: string
}

export interface Incident {
  id: string
  user_id: string
  analysis_id: string | null
  threat_type: ThreatType
  risk_score: number
  risk_level: RiskLevel
  confidence: number
  title: string
  description: string | null
  evidence: Record<string, unknown>
  explanation: string | null
  recommended_action: string | null
  status: IncidentStatus
  analyst_notes: string | null
  created_at: string
  updated_at: string
}

export interface Alert {
  id: string
  user_id: string
  analysis_id: string | null
  incident_id: string | null
  alert_type: string
  severity: RiskLevel
  title: string
  message: string
  is_read: boolean
  created_at: string
}

export interface AuditLog {
  id: string
  sequence: number
  event_type: string
  user_id: string | null
  analysis_id: string | null
  risk_score: number | null
  result_label: string | null
  details: string | null
  previous_hash: string
  current_hash: string
  created_at: string
}

export interface AuditChainVerifyResult {
  is_valid: boolean
  total_records: number
  verified_records: number
  first_broken_at: number | null
  message: string
}

export interface Watermark {
  id: string
  content_id: string
  owner: string
  content_hash: string
  filename: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface WatermarkVerifyResult {
  content_id: string
  is_authentic: boolean
  stored_hash: string | null
  computed_hash: string
  match: boolean
  message: string
  owner: string | null
  registered_at: string | null
}

export interface DashboardStats {
  total_analyses: number
  threats_detected: number
  high_risk_incidents: number
  critical_incidents: number
  phishing_detections: number
  deepfake_detections: number
  voice_clone_detections: number
  behavioral_anomalies: number
  open_incidents: number
  unread_alerts: number
  overall_risk_level: string
}

export interface ThreatTimeSeries {
  date: string
  phishing: number
  deepfake: number
  voice_clone: number
  anomaly: number
  total: number
}

export interface BehaviorRequest {
  login_hour?: number
  failed_attempts?: number
  is_new_device?: boolean
  is_unusual_location?: boolean
  access_frequency?: number
  session_duration_minutes?: number
  requests_per_minute?: number
}
