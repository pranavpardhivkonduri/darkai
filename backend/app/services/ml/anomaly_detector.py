"""
Behavioral Anomaly Detector
==============================
Implements real anomaly detection using Isolation Forest on behavioral features.

Input features:
  - login_hour: Hour of day (0–23) — deviations from typical pattern
  - failed_attempts: Recent failed login count
  - is_new_device: Boolean
  - is_unusual_location: Boolean (location change detected)
  - access_frequency: Access events per hour
  - session_duration_minutes: Session length
  - requests_per_minute: Request rate

The Isolation Forest is fit on a synthetic distribution representing normal
user behavior (low failed attempts, typical hours, known device, moderate rate).

Limitations (documented):
  - Reference distribution is synthetic. A production system would learn
    per-user baseline behavior from historical data.
  - Prototype for academic demonstration purposes.
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Feature order (must be consistent)
FEATURE_NAMES = [
    "login_hour_sin",     # encoded cyclically
    "login_hour_cos",
    "failed_attempts",
    "is_new_device",
    "is_unusual_location",
    "access_frequency",
    "session_duration_norm",
    "requests_per_minute",
]


def _encode_features(
    login_hour: int,
    failed_attempts: int,
    is_new_device: bool,
    is_unusual_location: bool,
    access_frequency: float,
    session_duration_minutes: float,
    requests_per_minute: float,
) -> np.ndarray:
    """Encode behavioral inputs into ML feature vector."""
    # Cyclic encoding for hour of day
    hour_sin = np.sin(2 * np.pi * login_hour / 24)
    hour_cos = np.cos(2 * np.pi * login_hour / 24)

    return np.array([
        hour_sin,
        hour_cos,
        min(failed_attempts, 10),           # cap at 10
        float(is_new_device),
        float(is_unusual_location),
        min(access_frequency, 100),
        min(session_duration_minutes, 480),  # cap at 8 hours
        min(requests_per_minute, 60),
    ], dtype=np.float32)


def _generate_normal_behavior(n_samples: int = 800) -> np.ndarray:
    """Generate synthetic reference for normal user behavior."""
    rng = np.random.RandomState(42)
    samples = []
    for _ in range(n_samples):
        # Normal: login during business hours, 0-1 failed attempts, known device, moderate rate
        login_hour = int(rng.normal(10, 3)) % 24  # skew towards daytime
        failed = max(0, int(rng.exponential(0.3)))
        new_device = rng.random() < 0.05          # 5% new device (normal)
        unusual_loc = rng.random() < 0.03         # 3% unusual location
        freq = max(0.1, rng.normal(5, 2))         # 5 requests/hour typical
        duration = max(5, rng.normal(45, 20))     # 45 min session
        rpm = max(0.1, rng.normal(2, 1))          # 2 requests/min
        samples.append(_encode_features(
            login_hour, failed, new_device, unusual_loc, freq, duration, rpm
        ))
    return np.array(samples)


class BehaviorAnomalyDetector:
    def __init__(self):
        self._model: Optional[IsolationForest] = None
        self._scaler: Optional[StandardScaler] = None
        self._train()

    def _train(self):
        normal_data = _generate_normal_behavior(n_samples=800)
        self._scaler = StandardScaler()
        scaled = self._scaler.fit_transform(normal_data)
        self._model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
        )
        self._model.fit(scaled)
        logger.info("Behavioral anomaly detector (Isolation Forest) trained")

    def detect(
        self,
        login_hour: int = 9,
        failed_attempts: int = 0,
        is_new_device: bool = False,
        is_unusual_location: bool = False,
        access_frequency: float = 5.0,
        session_duration_minutes: float = 45.0,
        requests_per_minute: float = 2.0,
    ) -> Dict[str, Any]:
        features = _encode_features(
            login_hour, failed_attempts, is_new_device,
            is_unusual_location, access_frequency,
            session_duration_minutes, requests_per_minute,
        )
        scaled = self._scaler.transform([features])

        # Raw Isolation Forest score (more negative = more anomalous)
        raw = float(self._model.score_samples(scaled)[0])
        # Normalize to 0-1 anomaly probability
        anomaly_prob = max(0.0, min(1.0, (-raw - 0.05) / 0.45))

        is_anomalous = anomaly_prob >= 0.5
        label = "Anomalous" if is_anomalous else "Normal"
        confidence = anomaly_prob if is_anomalous else (1.0 - anomaly_prob)
        risk_score = anomaly_prob * 100

        contributing = self._get_contributing_factors(
            login_hour, failed_attempts, is_new_device,
            is_unusual_location, access_frequency,
            session_duration_minutes, requests_per_minute,
            anomaly_prob
        )

        explanation = self._explain(label, contributing, confidence)

        return {
            "label": label,
            "anomaly_score": round(anomaly_prob, 4),
            "risk_score": round(risk_score, 1),
            "is_anomalous": is_anomalous,
            "confidence": round(confidence, 4),
            "contributing_factors": contributing,
            "explanation": explanation,
            "recommended_action": self._recommended_action(risk_score, contributing),
            "feature_values": {
                "login_hour": login_hour,
                "failed_attempts": failed_attempts,
                "is_new_device": is_new_device,
                "is_unusual_location": is_unusual_location,
                "access_frequency": round(access_frequency, 2),
                "session_duration_minutes": round(session_duration_minutes, 1),
                "requests_per_minute": round(requests_per_minute, 2),
            },
        }

    def _get_contributing_factors(
        self,
        login_hour: int,
        failed_attempts: int,
        is_new_device: bool,
        is_unusual_location: bool,
        access_frequency: float,
        session_duration_minutes: float,
        requests_per_minute: float,
        anomaly_prob: float,
    ) -> List[str]:
        factors = []

        # Unusual hour (night/early morning)
        if login_hour < 6 or login_hour > 22:
            factors.append(f"Login at unusual hour ({login_hour:02d}:00 — outside normal business hours)")

        # Failed attempts
        if failed_attempts >= 3:
            factors.append(f"Multiple failed login attempts ({failed_attempts})")
        elif failed_attempts >= 1 and anomaly_prob > 0.3:
            factors.append(f"Recent failed login attempt(s) ({failed_attempts})")

        # New device
        if is_new_device:
            factors.append("Login from unrecognized device")

        # Unusual location
        if is_unusual_location:
            factors.append("Login from unusual geographic location")

        # High request rate
        if requests_per_minute > 10:
            factors.append(f"High request rate ({requests_per_minute:.1f} req/min — possible automated activity)")

        # Very long session
        if session_duration_minutes > 240:
            factors.append(f"Unusually long session ({session_duration_minutes:.0f} minutes)")

        # High access frequency
        if access_frequency > 20:
            factors.append(f"High access frequency ({access_frequency:.1f}/hour)")

        if not factors and anomaly_prob >= 0.5:
            factors.append("Combined behavioral pattern deviates from established baseline")

        return factors

    def _explain(self, label: str, factors: List[str], confidence: float) -> str:
        conf_pct = round(confidence * 100)
        if label == "Normal":
            return (f"Behavior classified as normal ({conf_pct}% confidence). "
                    "Login time, device, location, and activity patterns are consistent with baseline.")
        factor_text = "; ".join(factors[:4]) if factors else "combined pattern deviation"
        return (f"Anomalous behavior detected ({conf_pct}% confidence). "
                f"Contributing factors: {factor_text}. "
                "This may indicate unauthorized access or account compromise.")

    def _recommended_action(self, risk_score: float, factors: List[str]) -> str:
        if risk_score < 30:
            return "Continue monitoring. No immediate action required."
        elif risk_score < 60:
            return "Log event for review. Consider sending a verification alert to the user."
        elif risk_score < 80:
            return "Require additional verification (MFA challenge). Flag for analyst review."
        else:
            return ("HIGH RISK: Consider session termination and account lockout. "
                    "Immediately escalate to security team for investigation.")


_detector: Optional[BehaviorAnomalyDetector] = None


def get_behavior_detector() -> BehaviorAnomalyDetector:
    global _detector
    if _detector is None:
        _detector = BehaviorAnomalyDetector()
    return _detector


def detect_anomaly(
    login_hour: int = 9,
    failed_attempts: int = 0,
    is_new_device: bool = False,
    is_unusual_location: bool = False,
    access_frequency: float = 5.0,
    session_duration_minutes: float = 45.0,
    requests_per_minute: float = 2.0,
) -> Dict[str, Any]:
    """Public interface for behavioral anomaly detection."""
    return get_behavior_detector().detect(
        login_hour, failed_attempts, is_new_device,
        is_unusual_location, access_frequency,
        session_duration_minutes, requests_per_minute,
    )
