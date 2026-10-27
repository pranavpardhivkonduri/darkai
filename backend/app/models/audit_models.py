import uuid
import hashlib
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class AuditLog(Base):
    """
    Tamper-evident hash-chain audit ledger.
    Each record hashes itself INCLUDING the previous record's hash.
    If any record is altered, chain verification fails.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid, index=True)
    sequence = Column(Float, nullable=False, index=True)  # monotonically increasing

    # What happened
    event_type = Column(String(64), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    analysis_id = Column(String(36), nullable=True)
    risk_score = Column(Float, nullable=True)
    result_label = Column(String(128), nullable=True)
    details = Column(Text, nullable=True)  # JSON string

    # Hash chain
    previous_hash = Column(String(64), nullable=False, default="0" * 64)
    current_hash = Column(String(64), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

    @staticmethod
    def compute_hash(
        sequence: float,
        event_type: str,
        user_id: str,
        analysis_id: str,
        risk_score: float,
        result_label: str,
        details: str,
        previous_hash: str,
        created_at: str,
    ) -> str:
        """Deterministically hash all fields including previous_hash."""
        payload = json.dumps({
            "sequence": sequence,
            "event_type": event_type,
            "user_id": user_id,
            "analysis_id": analysis_id,
            "risk_score": risk_score,
            "result_label": result_label,
            "details": details,
            "previous_hash": previous_hash,
            "created_at": created_at,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
