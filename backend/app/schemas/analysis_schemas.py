from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.analysis_models import (
    ThreatType, AnalysisInputType, RiskLevel, IncidentStatus
)


# ─── Analysis ──────────────────────────────────────────────
class AnalysisResultOut(BaseModel):
    id: str
    user_id: str
    input_type: AnalysisInputType
    threat_type: ThreatType
    filename: Optional[str]
    raw_input: Optional[str]
    label: str
    confidence: float
    risk_score: float
    risk_level: RiskLevel
    indicators: List[str]
    explanation: Optional[str]
    recommended_action: Optional[str]
    model_features: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Text / URL Analyze ────────────────────────────────────
class TextAnalyzeRequest(BaseModel):
    content: str
    content_type: str = "email"  # email | sms | chat | social | url


class URLAnalyzeRequest(BaseModel):
    url: str


# ─── Behavior ──────────────────────────────────────────────
class BehaviorAnalyzeRequest(BaseModel):
    login_hour: Optional[int] = None          # 0-23
    failed_attempts: Optional[int] = 0
    is_new_device: Optional[bool] = False
    is_unusual_location: Optional[bool] = False
    access_frequency: Optional[float] = 1.0   # accesses/hour
    session_duration_minutes: Optional[float] = 30.0
    requests_per_minute: Optional[float] = 1.0


class BehaviorResultOut(BaseModel):
    label: str
    anomaly_score: float
    risk_score: float
    risk_level: RiskLevel
    is_anomalous: bool
    contributing_factors: List[str]
    explanation: str
    recommended_action: str


# ─── Incidents ─────────────────────────────────────────────
class IncidentOut(BaseModel):
    id: str
    user_id: str
    analysis_id: Optional[str]
    threat_type: ThreatType
    risk_score: float
    risk_level: RiskLevel
    confidence: float
    title: str
    description: Optional[str]
    evidence: Dict[str, Any]
    explanation: Optional[str]
    recommended_action: Optional[str]
    status: IncidentStatus
    analyst_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
    analyst_notes: Optional[str] = None


# ─── Risk ──────────────────────────────────────────────────
class RiskScoreOut(BaseModel):
    id: str
    user_id: str
    analysis_id: Optional[str]
    overall_score: float
    risk_level: RiskLevel
    phishing_score: float
    deepfake_score: float
    voice_score: float
    anomaly_score: float
    auth_risk: float
    contributing_factors: List[str]
    recommended_action: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Alerts ────────────────────────────────────────────────
class AlertOut(BaseModel):
    id: str
    user_id: str
    analysis_id: Optional[str]
    incident_id: Optional[str]
    alert_type: str
    severity: RiskLevel
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Watermark ─────────────────────────────────────────────
class WatermarkCreateRequest(BaseModel):
    owner: str
    content_id: str
    metadata: Optional[Dict[str, Any]] = {}


class WatermarkOut(BaseModel):
    id: str
    content_id: str
    owner: str
    content_hash: str
    filename: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class WatermarkVerifyResult(BaseModel):
    content_id: str
    is_authentic: bool
    stored_hash: str
    computed_hash: str
    match: bool
    message: str
    owner: Optional[str]
    registered_at: Optional[datetime]


# ─── Audit ─────────────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: str
    sequence: float
    event_type: str
    user_id: Optional[str]
    analysis_id: Optional[str]
    risk_score: Optional[float]
    result_label: Optional[str]
    details: Optional[str]
    previous_hash: str
    current_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditChainVerifyResult(BaseModel):
    is_valid: bool
    total_records: int
    verified_records: int
    first_broken_at: Optional[int]
    message: str


# ─── Dashboard ─────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_analyses: int
    threats_detected: int
    high_risk_incidents: int
    critical_incidents: int
    phishing_detections: int
    deepfake_detections: int
    voice_clone_detections: int
    behavioral_anomalies: int
    open_incidents: int
    unread_alerts: int
    overall_risk_level: str


class ThreatTimeSeries(BaseModel):
    date: str
    phishing: int
    deepfake: int
    voice_clone: int
    anomaly: int
    total: int
