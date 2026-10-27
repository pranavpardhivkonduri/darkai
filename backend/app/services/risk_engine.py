"""
Central Risk Assessment Engine
================================
Combines scores from all detectors into a single overall risk score.
Thresholds are read from settings — not scattered across code.
"""

from typing import Dict, Any, List, Optional
from app.config import settings


def calculate_risk(
    phishing_score: float = 0.0,
    deepfake_score: float = 0.0,
    voice_score: float = 0.0,
    anomaly_score: float = 0.0,
    auth_risk: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Weighted combination of component risk scores.
    
    Parameters:
        phishing_score: 0-100
        deepfake_score: 0-100
        voice_score: 0-100
        anomaly_score: 0-100
        auth_risk: 0-100
        weights: Optional custom weights (must sum to 1)

    Returns:
        Dict with overall_score, risk_level, contributing_factors, recommended_action
    """
    if weights is None:
        weights = {
            "phishing": 0.35,
            "deepfake": 0.25,
            "voice": 0.20,
            "anomaly": 0.15,
            "auth": 0.05,
        }

    scores = {
        "phishing": phishing_score,
        "deepfake": deepfake_score,
        "voice": voice_score,
        "anomaly": anomaly_score,
        "auth": auth_risk,
    }

    overall = sum(scores[k] * weights[k] for k in scores)
    overall = round(min(overall, 100.0), 1)

    risk_level = settings.get_risk_level(overall)

    contributing = _get_contributing_factors(scores, weights)
    recommended = _recommended_action(risk_level, scores)

    return {
        "overall_score": overall,
        "risk_level": risk_level,
        "component_scores": {
            "phishing_score": round(phishing_score, 1),
            "deepfake_score": round(deepfake_score, 1),
            "voice_score": round(voice_score, 1),
            "anomaly_score": round(anomaly_score, 1),
            "auth_risk": round(auth_risk, 1),
        },
        "contributing_factors": contributing,
        "recommended_action": recommended,
    }


def _get_contributing_factors(
    scores: Dict[str, float],
    weights: Dict[str, float],
) -> List[str]:
    """Explain which components contribute most to overall risk."""
    factors = []
    labels = {
        "phishing": "Phishing/Social Engineering",
        "deepfake": "Visual Manipulation (Deepfake)",
        "voice": "Voice Synthesis (Clone)",
        "anomaly": "Behavioral Anomaly",
        "auth": "Authentication Risk",
    }
    # Sort by weighted contribution
    contributions = {
        k: scores[k] * weights.get(k, 0.1)
        for k in scores
        if scores[k] > 10
    }
    for k in sorted(contributions, key=contributions.get, reverse=True):
        s = scores[k]
        if s >= 60:
            factors.append(f"{labels[k]}: {round(s)}% risk (HIGH)")
        elif s >= 30:
            factors.append(f"{labels[k]}: {round(s)}% risk (MEDIUM)")
    return factors if factors else ["No significant individual risk factors"]


def _recommended_action(risk_level: str, scores: Dict[str, float]) -> str:
    actions = {
        "LOW": "Allow action. Log for monitoring.",
        "MEDIUM": "Issue warning to user. Enable enhanced monitoring.",
        "HIGH": "Require additional authentication. Flag for analyst review.",
        "CRITICAL": "Restrict access immediately. Create critical incident. Mandatory analyst review.",
    }
    return actions.get(risk_level, "Review manually")


def compute_auth_risk(failed_attempts: int, is_new_device: bool, unusual_location: bool) -> float:
    """Simple auth-risk helper for login events."""
    score = 0.0
    score += min(failed_attempts * 15, 60)
    if is_new_device:
        score += 20
    if unusual_location:
        score += 20
    return min(score, 100.0)
