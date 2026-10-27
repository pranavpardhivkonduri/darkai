"""
Tamper-Evident Audit Ledger Service
======================================
Each audit event hashes its own data AND the previous event's hash.
If any stored record is tampered with, chain verification will detect it.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.audit_models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_event(
    db: Session,
    event_type: str,
    user_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    risk_score: Optional[float] = None,
    result_label: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Append a new event to the audit chain."""

    # Get last record for previous hash
    last = db.query(AuditLog).order_by(AuditLog.sequence.desc()).first()
    sequence = (last.sequence + 1) if last else 1.0
    previous_hash = last.current_hash if last else ("0" * 64)

    created_at = datetime.utcnow()
    details_str = json.dumps(details or {}, sort_keys=True)

    current_hash = AuditLog.compute_hash(
        sequence=sequence,
        event_type=event_type,
        user_id=user_id or "",
        analysis_id=analysis_id or "",
        risk_score=risk_score or 0.0,
        result_label=result_label or "",
        details=details_str,
        previous_hash=previous_hash,
        created_at=created_at.isoformat(),
    )

    entry = AuditLog(
        sequence=sequence,
        event_type=event_type,
        user_id=user_id,
        analysis_id=analysis_id,
        risk_score=risk_score,
        result_label=result_label,
        details=details_str,
        previous_hash=previous_hash,
        current_hash=current_hash,
        created_at=created_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.debug(f"Audit event created: {event_type} seq={sequence} hash={current_hash[:8]}...")
    return entry


def verify_audit_chain(db: Session) -> Dict[str, Any]:
    """
    Verify the entire audit chain by recomputing each record's hash and
    checking it matches the stored hash and the next record's previous_hash.
    """
    records = db.query(AuditLog).order_by(AuditLog.sequence.asc()).all()
    total = len(records)

    if total == 0:
        return {
            "is_valid": True,
            "total_records": 0,
            "verified_records": 0,
            "first_broken_at": None,
            "message": "No audit records to verify.",
        }

    verified = 0
    first_broken = None

    for i, rec in enumerate(records):
        expected = AuditLog.compute_hash(
            sequence=rec.sequence,
            event_type=rec.event_type,
            user_id=rec.user_id or "",
            analysis_id=rec.analysis_id or "",
            risk_score=rec.risk_score or 0.0,
            result_label=rec.result_label or "",
            details=rec.details or "{}",
            previous_hash=rec.previous_hash,
            created_at=rec.created_at.isoformat(),
        )

        if expected != rec.current_hash:
            if first_broken is None:
                first_broken = int(rec.sequence)
            logger.warning(f"Audit chain broken at sequence {rec.sequence}")
        else:
            # Also verify chain linkage (next record's previous_hash)
            if i + 1 < total:
                next_rec = records[i + 1]
                if next_rec.previous_hash != rec.current_hash:
                    if first_broken is None:
                        first_broken = int(next_rec.sequence)
                    logger.warning(f"Chain linkage broken at sequence {next_rec.sequence}")
                else:
                    verified += 1
            else:
                verified += 1

    is_valid = first_broken is None
    return {
        "is_valid": is_valid,
        "total_records": total,
        "verified_records": verified,
        "first_broken_at": first_broken,
        "message": (
            "AUDIT CHAIN VALID — All records verified. No tampering detected."
            if is_valid
            else f"AUDIT CHAIN COMPROMISED — Integrity failure detected at record #{first_broken}."
        ),
    }
