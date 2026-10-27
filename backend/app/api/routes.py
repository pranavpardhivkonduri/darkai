"""
Dashboard, Incidents, Alerts, Watermark, Audit, and Report API Routers
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.auth.dependencies import get_current_user, require_analyst, require_admin
from app.models.user_models import User, Role
from app.models.analysis_models import (
    AnalysisResult, Incident, Alert, RiskScore, Watermark,
    ThreatType, RiskLevel, IncidentStatus
)
from app.models.audit_models import AuditLog
from app.schemas.analysis_schemas import (
    DashboardStats, IncidentOut, IncidentStatusUpdate,
    AlertOut, WatermarkOut, WatermarkCreateRequest,
    WatermarkVerifyResult, AuditLogOut, AuditChainVerifyResult,
)
from app.services.watermark_service import create_watermark, verify_watermark
from app.services.audit_service import create_audit_event, verify_audit_chain as _verify_chain
from app.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard_router.get("/statistics", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(AnalysisResult)
    if current_user.role == Role.USER:
        q = q.filter(AnalysisResult.user_id == current_user.id)

    total = q.count()
    threats = q.filter(AnalysisResult.risk_score >= 30).count()
    high_risk = q.filter(AnalysisResult.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])).count()
    critical = q.filter(AnalysisResult.risk_level == RiskLevel.CRITICAL).count()
    phishing = q.filter(AnalysisResult.threat_type == ThreatType.PHISHING).count()
    deepfake = q.filter(AnalysisResult.threat_type == ThreatType.DEEPFAKE).count()
    voice = q.filter(AnalysisResult.threat_type == ThreatType.VOICE_CLONE).count()
    anomaly = q.filter(AnalysisResult.threat_type == ThreatType.ANOMALY).count()

    iq = db.query(Incident)
    if current_user.role == Role.USER:
        iq = iq.filter(Incident.user_id == current_user.id)
    open_incidents = iq.filter(Incident.status == IncidentStatus.OPEN).count()

    aq = db.query(Alert)
    if current_user.role == Role.USER:
        aq = aq.filter(Alert.user_id == current_user.id)
    unread_alerts = aq.filter(Alert.is_read == False).count()

    # Overall risk level based on recent high-risk events
    recent = q.filter(
        AnalysisResult.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(AnalysisResult.risk_score.desc()).first()
    overall_risk = settings.get_risk_level(recent.risk_score if recent else 0)

    return DashboardStats(
        total_analyses=total,
        threats_detected=threats,
        high_risk_incidents=high_risk,
        critical_incidents=critical,
        phishing_detections=phishing,
        deepfake_detections=deepfake,
        voice_clone_detections=voice,
        behavioral_anomalies=anomaly,
        open_incidents=open_incidents,
        unread_alerts=unread_alerts,
        overall_risk_level=overall_risk,
    )


@dashboard_router.get("/timeline")
def get_threat_timeline(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return per-day threat counts for the last N days."""
    result = []
    for i in range(days - 1, -1, -1):
        day_start = (datetime.utcnow() - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        q = db.query(AnalysisResult).filter(
            AnalysisResult.created_at >= day_start,
            AnalysisResult.created_at < day_end,
        )
        if current_user.role == Role.USER:
            q = q.filter(AnalysisResult.user_id == current_user.id)

        all_rows = q.all()
        result.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "phishing": sum(1 for r in all_rows if r.threat_type == ThreatType.PHISHING),
            "deepfake": sum(1 for r in all_rows if r.threat_type == ThreatType.DEEPFAKE),
            "voice_clone": sum(1 for r in all_rows if r.threat_type == ThreatType.VOICE_CLONE),
            "anomaly": sum(1 for r in all_rows if r.threat_type == ThreatType.ANOMALY),
            "total": len(all_rows),
        })
    return result


# ═══════════════════════════════════════════════════════════
# INCIDENTS
# ═══════════════════════════════════════════════════════════
incident_router = APIRouter(prefix="/incidents", tags=["Incidents"])


@incident_router.get("", response_model=List[IncidentOut])
def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    status: Optional[IncidentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Incident)
    if current_user.role == Role.USER:
        q = q.filter(Incident.user_id == current_user.id)
    if status:
        q = q.filter(Incident.status == status)
    return q.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()


@incident_router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if current_user.role == Role.USER and inc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return inc


@incident_router.post("/{incident_id}/status", response_model=IncidentOut)
def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_status = inc.status
    inc.status = payload.status
    if payload.analyst_notes:
        inc.analyst_notes = payload.analyst_notes
    inc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inc)

    create_audit_event(
        db, "INCIDENT_STATUS_UPDATE",
        user_id=current_user.id,
        analysis_id=incident_id,
        result_label=f"{old_status.value} → {payload.status.value}",
        details={"notes": payload.analyst_notes},
    )
    return inc


# ═══════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════
alert_router = APIRouter(prefix="/alerts", tags=["Alerts"])


@alert_router.get("", response_model=List[AlertOut])
def list_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if current_user.role == Role.USER:
        q = q.filter(Alert.user_id == current_user.id)
    if unread_only:
        q = q.filter(Alert.is_read == False)
    return q.order_by(Alert.created_at.desc()).limit(100).all()


@alert_router.post("/{alert_id}/read")
def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}


# ═══════════════════════════════════════════════════════════
# WATERMARK
# ═══════════════════════════════════════════════════════════
watermark_router = APIRouter(prefix="/watermark", tags=["Watermark"])


@watermark_router.post("/create", response_model=WatermarkOut)
def create_watermark_endpoint(
    file: UploadFile = File(...),
    owner: str = Form(...),
    content_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    if len(content) > settings.max_file_bytes():
        raise HTTPException(status_code=413, detail="File too large")

    try:
        wm = create_watermark(
            db=db,
            user_id=current_user.id,
            content_bytes=content,
            content_id=content_id,
            owner=owner,
            filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    create_audit_event(
        db, "WATERMARK_CREATED",
        user_id=current_user.id,
        result_label=content_id,
        details={"owner": owner, "filename": file.filename},
    )
    return wm


@watermark_router.post("/verify", response_model=WatermarkVerifyResult)
def verify_watermark_endpoint(
    file: UploadFile = File(...),
    content_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    result = verify_watermark(db=db, content_bytes=content, content_id=content_id)
    create_audit_event(
        db, "WATERMARK_VERIFIED",
        user_id=current_user.id,
        result_label="AUTHENTIC" if result["is_authentic"] else "MODIFIED",
        details={"content_id": content_id},
    )
    return result


@watermark_router.get("", response_model=List[WatermarkOut])
def list_watermarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Watermark)
    if current_user.role == Role.USER:
        q = q.filter(Watermark.user_id == current_user.id)
    return q.order_by(Watermark.created_at.desc()).all()


# ═══════════════════════════════════════════════════════════
# AUDIT LEDGER
# ═══════════════════════════════════════════════════════════
audit_router = APIRouter(prefix="/audit", tags=["Audit"])


@audit_router.get("/logs", response_model=List[AuditLogOut])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    _: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.sequence.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@audit_router.post("/verify", response_model=AuditChainVerifyResult)
def verify_audit(
    _: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    return _verify_chain(db)


# ═══════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════
report_router = APIRouter(prefix="/reports", tags=["Reports"])


@report_router.post("/generate/{incident_id}")
def generate_report(
    incident_id: str,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
):
    """Generate a text/JSON report for an incident."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == inc.analysis_id).first()
    user = db.query(User).filter(User.id == inc.user_id).first()

    report = {
        "report_generated": datetime.utcnow().isoformat(),
        "generated_by": current_user.username,
        "incident": {
            "id": inc.id,
            "title": inc.title,
            "status": inc.status.value,
            "threat_type": inc.threat_type.value,
            "risk_score": inc.risk_score,
            "risk_level": inc.risk_level.value,
            "confidence": inc.confidence,
            "created_at": inc.created_at.isoformat(),
            "analyst_notes": inc.analyst_notes,
            "explanation": inc.explanation,
            "recommended_action": inc.recommended_action,
            "evidence": inc.evidence,
        },
        "user": {"id": inc.user_id, "username": user.username if user else "unknown"},
        "analysis": {
            "id": analysis.id if analysis else None,
            "input_type": analysis.input_type.value if analysis else None,
            "label": analysis.label if analysis else None,
            "indicators": analysis.indicators if analysis else [],
        } if analysis else None,
        "disclaimer": (
            "DarkAI provides automated risk indicators for cybersecurity analysis. "
            "Results should be reviewed by qualified personnel before being treated "
            "as definitive evidence of malicious activity."
        ),
    }

    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    filename = f"report_{incident_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(settings.REPORTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    create_audit_event(
        db, "REPORT_GENERATED",
        user_id=current_user.id,
        analysis_id=incident_id,
        result_label=filename,
    )

    return {"message": "Report generated", "filename": filename, "report": report}
