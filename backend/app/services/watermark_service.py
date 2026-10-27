"""
Digital Watermarking Service
================================
Provides content provenance/integrity via SHA-256 hash-based watermarking.

How it works:
  CREATE:
    - Compute SHA-256 of file content
    - Store hash + owner + content_id + metadata in database
    - Return content_id and hash as the "watermark record"

  VERIFY:
    - Re-compute SHA-256 of uploaded content
    - Compare against stored hash for the content_id
    - Return AUTHENTIC if match, MODIFIED if mismatch

Note: This is a cryptographic hash-based provenance system, NOT
steganographic watermarking (embedding invisible bits in the image).
It demonstrates the integrity/provenance concept used in media authentication.
"""

import hashlib
import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.analysis_models import Watermark

logger = logging.getLogger(__name__)


def compute_content_hash(content_bytes: bytes) -> str:
    """Compute SHA-256 hash of content bytes."""
    return hashlib.sha256(content_bytes).hexdigest()


def create_watermark(
    db: Session,
    user_id: str,
    content_bytes: bytes,
    content_id: str,
    owner: str,
    filename: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Watermark:
    """Register content provenance in the watermark ledger."""
    content_hash = compute_content_hash(content_bytes)

    # Check if content_id already exists
    existing = db.query(Watermark).filter(Watermark.content_id == content_id).first()
    if existing:
        raise ValueError(f"Content ID '{content_id}' is already registered")

    wm = Watermark(
        user_id=user_id,
        content_id=content_id,
        owner=owner,
        content_hash=content_hash,
        filename=filename,
        extra_metadata=metadata or {},
    )
    db.add(wm)
    db.commit()
    db.refresh(wm)
    logger.info(f"Watermark created: {content_id} hash={content_hash[:12]}...")
    return wm


def verify_watermark(
    db: Session,
    content_bytes: bytes,
    content_id: str,
) -> dict:
    """Verify content integrity against stored watermark."""
    computed = compute_content_hash(content_bytes)

    record = db.query(Watermark).filter(Watermark.content_id == content_id).first()
    if not record:
        return {
            "content_id": content_id,
            "is_authentic": False,
            "stored_hash": None,
            "computed_hash": computed,
            "match": False,
            "message": "No watermark record found for this content ID. Content is unregistered.",
            "owner": None,
            "registered_at": None,
        }

    match = computed == record.content_hash
    return {
        "content_id": content_id,
        "is_authentic": match,
        "stored_hash": record.content_hash,
        "computed_hash": computed,
        "match": match,
        "message": (
            "AUTHENTIC — Content matches registered watermark. No modification detected."
            if match
            else "MODIFIED — Content hash does not match registered watermark. Content may have been altered."
        ),
        "owner": record.owner,
        "registered_at": record.created_at,
    }
