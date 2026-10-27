"""
Analysis API Router
- POST /analyze/text   (phishing / NLP)
- POST /analyze/url    (URL phishing)
- POST /analyze/image  (deepfake image)
- POST /analyze/video  (deepfake video)
- POST /analyze/audio  (voice clone)
- POST /analyze/behavior (anomaly)
- GET  /analysis       (history)
- GET  /analysis/{id}
"""

import os
import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.auth.dependencies import get_current_user
from app.models.user_models import User
from app.models.analysis_models import (
    AnalysisResult, Incident, Alert, RiskScore,
    ThreatType, AnalysisInputType, RiskLevel, IncidentStatus
)
from app.schemas.analysis_schemas import (
    AnalysisResultOut, TextAnalyzeRequest, BehaviorAnalyzeRequest, BehaviorResultOut
)
from app.services.ml.phishing_detector import predict_phishing
from app.services.ml.deepfake_detector import predict_deepfake, predict_deepfake_video
from app.services.ml.voice_detector import predict_voice_clone
from app.services.ml.anomaly_detector import detect_anomaly
from app.services.risk_engine import calculate_risk
from app.services.audit_service import create_audit_event
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])

UPLOAD_DIR = settings.UPLOAD_DIR


def _save_upload(upload: UploadFile, subdir: str) -> tuple[str, bytes]:
    """Validate and save uploaded file. Returns (path, bytes)."""
    content = upload.file.read()

    if len(content) > settings.max_file_bytes():
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    ext = os.path.splitext(upload.filename or "")[-1].lower().lstrip(".")
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    dirpath = os.path.join(UPLOAD_DIR, subdir)
    os.makedirs(dirpath, exist_ok=True)
    filepath = os.path.join(dirpath, safe_name)

    with open(filepath, "wb") as f:
        f.write(content)

    return filepath, content


def _validate_extension(filename: str, allowed: List[str]):
    ext = os.path.splitext(filename or "")[-1].lower().lstrip(".")
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Allowed: {allowed}"
        )


def _get_risk_level(score: float) -> RiskLevel:
    level = settings.get_risk_level(score)
    return RiskLevel(level)


def _create_incident_if_needed(
    db: Session,
    user: User,
    result: AnalysisResult,
    threshold: float = 60.0,
):
    """Auto-create incident for high/critical risk results."""
    if result.risk_score < threshold:
        return

    incident = Incident(
        user_id=user.id,
        analysis_id=result.id,
        threat_type=result.threat_type,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        confidence=result.confidence,
        title=f"[AUTO] {result.threat_type.value} — Risk {result.risk_score:.0f}/100",
        description=result.explanation,
        evidence={"label": result.label, "indicators": result.indicators},
        explanation=result.explanation,
        recommended_action=result.recommended_action,
        status=IncidentStatus.OPEN,
    )
    db.add(incident)

    # Create alert
    severity = _get_risk_level(result.risk_score)
    alert = Alert(
        user_id=user.id,
        analysis_id=result.id,
        alert_type=result.threat_type.value,
        severity=severity,
        title=f"Threat detected: {result.threat_type.value}",
        message=(f"Risk {result.risk_score:.0f}/100 — {result.label}. "
                 f"{result.recommended_action or 'Review required.'}"),
    )
    db.add(alert)
    db.commit()


# ─── Text / Phishing ───────────────────────────────────────────────────────
@router.post("/text", response_model=AnalysisResultOut)
def analyze_text(
    payload: TextAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result_data = predict_phishing(payload.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.TEXT,
        threat_type=ThreatType.PHISHING,
        raw_input=payload.content[:1000],  # truncate for storage
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("indicators", []),
        explanation=result_data.get("explanation"),
        recommended_action=_recommended_action_text(risk_level),
        model_features=result_data.get("class_probabilities", {}),
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar)
    create_audit_event(
        db, "PHISHING_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
        details={"input_type": "text", "content_type": payload.content_type},
    )

    return ar


# ─── URL ────────────────────────────────────────────────────────────────────
class URLPayload(BaseModel):
    url: str

@router.post("/url", response_model=AnalysisResultOut)
def analyze_url(
    payload: URLPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result_data = predict_phishing(text="", url=payload.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.URL,
        threat_type=ThreatType.PHISHING,
        raw_input=payload.url[:2000],
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("indicators", []),
        explanation=result_data.get("explanation"),
        recommended_action=_recommended_action_text(risk_level),
        model_features=result_data.get("url_features", {}),
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar)
    create_audit_event(
        db, "URL_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
    )
    return ar


# ─── Image (Deepfake) ───────────────────────────────────────────────────────
@router.post("/image", response_model=AnalysisResultOut)
def analyze_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_extension(file.filename, settings.get_allowed_images())
    filepath, content = _save_upload(file, "images")

    try:
        result_data = predict_deepfake(content, file.filename)
    except Exception as e:
        logger.error(f"Deepfake analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.IMAGE,
        threat_type=ThreatType.DEEPFAKE,
        filename=file.filename,
        file_path=filepath,
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("indicators", []),
        explanation=result_data.get("explanation"),
        recommended_action=result_data.get("recommended_action"),
        model_features={"frames_analyzed": result_data.get("frames_analyzed", 1)},
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar)
    create_audit_event(
        db, "DEEPFAKE_IMAGE_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
    )
    return ar


# ─── Video (Deepfake) ──────────────────────────────────────────────────────
@router.post("/video", response_model=AnalysisResultOut)
def analyze_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_extension(file.filename, settings.get_allowed_video())
    filepath, _ = _save_upload(file, "videos")

    try:
        result_data = predict_deepfake_video(filepath)
    except Exception as e:
        logger.error(f"Video deepfake error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.VIDEO,
        threat_type=ThreatType.DEEPFAKE,
        filename=file.filename,
        file_path=filepath,
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("indicators", []),
        explanation=result_data.get("explanation"),
        recommended_action=result_data.get("recommended_action"),
        model_features={
            "frames_analyzed": result_data.get("frames_analyzed", 0),
            "total_frames": result_data.get("total_frames", 0),
        },
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar)
    create_audit_event(
        db, "DEEPFAKE_VIDEO_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
        details={"frames_analyzed": result_data.get("frames_analyzed")},
    )
    return ar


# ─── Audio (Voice Clone) ───────────────────────────────────────────────────
@router.post("/audio", response_model=AnalysisResultOut)
def analyze_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_extension(file.filename, settings.get_allowed_audio())
    filepath, content = _save_upload(file, "audio")

    try:
        result_data = predict_voice_clone(content, file.filename)
    except Exception as e:
        logger.error(f"Voice clone analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.AUDIO,
        threat_type=ThreatType.VOICE_CLONE,
        filename=file.filename,
        file_path=filepath,
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("indicators", []),
        explanation=result_data.get("explanation"),
        recommended_action=result_data.get("recommended_action"),
        model_features=result_data.get("audio_features", {}),
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar)
    create_audit_event(
        db, "VOICE_CLONE_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
    )
    return ar


# ─── Behavior ─────────────────────────────────────────────────────────────
@router.post("/behavior", response_model=AnalysisResultOut)
def analyze_behavior(
    payload: BehaviorAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result_data = detect_anomaly(
            login_hour=payload.login_hour or 9,
            failed_attempts=payload.failed_attempts or 0,
            is_new_device=payload.is_new_device or False,
            is_unusual_location=payload.is_unusual_location or False,
            access_frequency=payload.access_frequency or 1.0,
            session_duration_minutes=payload.session_duration_minutes or 30.0,
            requests_per_minute=payload.requests_per_minute or 1.0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk_score = result_data["risk_score"]
    risk_level = _get_risk_level(risk_score)

    ar = AnalysisResult(
        user_id=current_user.id,
        input_type=AnalysisInputType.BEHAVIOR,
        threat_type=ThreatType.ANOMALY,
        raw_input=str(payload.model_dump()),
        label=result_data["label"],
        confidence=result_data["confidence"],
        risk_score=risk_score,
        risk_level=risk_level,
        indicators=result_data.get("contributing_factors", []),
        explanation=result_data.get("explanation"),
        recommended_action=result_data.get("recommended_action"),
        model_features=result_data.get("feature_values", {}),
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    _create_incident_if_needed(db, current_user, ar, threshold=50.0)
    create_audit_event(
        db, "BEHAVIOR_ANALYSIS",
        user_id=current_user.id,
        analysis_id=ar.id,
        risk_score=risk_score,
        result_label=ar.label,
    )
    return ar


# ─── History ──────────────────────────────────────────────────────────────
@router.get("", response_model=List[AnalysisResultOut])
def list_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.user_models import Role
    q = db.query(AnalysisResult)
    if current_user.role == Role.USER:
        q = q.filter(AnalysisResult.user_id == current_user.id)
    return q.order_by(AnalysisResult.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{analysis_id}", response_model=AnalysisResultOut)
def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ar = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    if not ar:
        raise HTTPException(status_code=404, detail="Analysis not found")
    from app.models.user_models import Role
    if current_user.role == Role.USER and ar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return ar


def _recommended_action_text(risk_level: RiskLevel) -> str:
    actions = {
        RiskLevel.LOW: "No action required. Continue monitoring.",
        RiskLevel.MEDIUM: "Review the message. Do not click links or provide information until verified.",
        RiskLevel.HIGH: "Do not interact. Report to security team. Flag for analyst review.",
        RiskLevel.CRITICAL: "Immediate threat. Do not interact. Isolate and escalate to security team.",
    }
    return actions.get(risk_level, "Review manually")
