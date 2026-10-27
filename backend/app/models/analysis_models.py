import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, DateTime, Enum, Integer,
    Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship
from app.database.db import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ThreatType(str, enum.Enum):
    DEEPFAKE = "DEEPFAKE"
    VOICE_CLONE = "VOICE_CLONE"
    PHISHING = "PHISHING"
    ANOMALY = "ANOMALY"
    WATERMARK = "WATERMARK"
    UNKNOWN = "UNKNOWN"


class AnalysisInputType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    URL = "URL"
    BEHAVIOR = "BEHAVIOR"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=gen_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_type = Column(Enum(AnalysisInputType), nullable=False)
    threat_type = Column(Enum(ThreatType), nullable=False)

    # File info (if applicable)
    filename = Column(String(512), nullable=True)
    file_path = Column(String(1024), nullable=True)

    # Raw input
    raw_input = Column(Text, nullable=True)

    # Prediction
    label = Column(String(128), nullable=False)
    confidence = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)

    # Detail
    indicators = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    model_features = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analyses")
    incident = relationship("Incident", back_populates="analysis", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=gen_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_results.id"), nullable=True)

    threat_type = Column(Enum(ThreatType), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    confidence = Column(Float, nullable=False)

    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(JSON, default=dict)
    explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)

    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    analyst_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="incidents")
    analysis = relationship("AnalysisResult", back_populates="incident")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_results.id"), nullable=True)

    overall_score = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    phishing_score = Column(Float, default=0.0)
    deepfake_score = Column(Float, default=0.0)
    voice_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    auth_risk = Column(Float, default=0.0)
    contributing_factors = Column(JSON, default=list)
    recommended_action = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "system_alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_id = Column(String(36), ForeignKey("analysis_results.id"), nullable=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True)

    alert_type = Column(String(64), nullable=False)
    severity = Column(Enum(RiskLevel), nullable=False)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class Watermark(Base):
    __tablename__ = "watermarks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    content_id = Column(String(256), nullable=False, unique=True, index=True)
    owner = Column(String(256), nullable=False)
    content_hash = Column(String(64), nullable=False)
    filename = Column(String(512), nullable=True)
    extra_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def metadata(self):
        return self.extra_metadata or {}

    user = relationship("User", back_populates="watermarks")


class BehaviorEvent(Base):
    __tablename__ = "behavior_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    login_hour = Column(Integer, nullable=True)
    failed_attempts = Column(Integer, default=0)
    is_new_device = Column(Boolean, default=False)
    is_unusual_location = Column(Boolean, default=False)
    access_frequency = Column(Float, default=1.0)
    session_duration_minutes = Column(Float, default=30.0)
    requests_per_minute = Column(Float, default=1.0)

    anomaly_score = Column(Float, nullable=True)
    is_anomalous = Column(Boolean, default=False)
    contributing_factors = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="behavior_events")
