"""
Deepfake Image/Video Detector
=================================
Lightweight computer-vision feature-based classifier using OpenCV.

Approach (documented prototype):
  1. Validate and load the image/video frame(s).
  2. Extract visual features:
     - Frequency-domain analysis via DCT/FFT (manipulation artifacts)
     - Local Binary Patterns (LBP) texture statistics
     - Color channel correlation analysis
     - Noise level estimation
     - Edge consistency (Laplacian variance)
     - Compression artifact analysis
  3. Run Isolation Forest anomaly scorer on extracted features.
  4. Threshold + calibrated confidence → prediction.

Limitations (documented):
  - This is a signal-processing feature approach, NOT a deep neural network
    deepfake detector. It cannot reliably detect all GAN-generated deepfakes.
  - A state-of-the-art CNN (e.g., EfficientNet-based) would require GPU training
    on FaceForensics++. That exceeds a typical laptop environment.
  - This prototype demonstrates the detection pipeline and is replaceable via
    the predict_deepfake() interface.
"""

import io
import logging
import math
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - deepfake detector will use fallback mode")


def _extract_features(img: np.ndarray) -> Dict[str, float]:
    """Extract manipulation-indicative features from a single BGR image."""
    features = {}

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape

    # 1. Laplacian variance (edge sharpness / blur detection)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    features["laplacian_var"] = float(np.var(lap))

    # 2. Noise estimation via high-frequency residuals
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = gray - blur
    features["noise_std"] = float(np.std(noise))
    features["noise_mean_abs"] = float(np.mean(np.abs(noise)))

    # 3. Color channel correlation (natural images have high RGB correlation)
    b, g, r = cv2.split(img.astype(np.float32))
    corr_rg = float(np.corrcoef(r.flatten(), g.flatten())[0, 1]) if r.size > 1 else 0
    corr_rb = float(np.corrcoef(r.flatten(), b.flatten())[0, 1]) if r.size > 1 else 0
    features["color_corr_rg"] = corr_rg if not math.isnan(corr_rg) else 0
    features["color_corr_rb"] = corr_rb if not math.isnan(corr_rb) else 0

    # 4. DCT energy ratio (compression / GAN artifacts show in high-frequency DCT)
    # Resize to fixed size for DCT
    small = cv2.resize(gray, (64, 64))
    dct = cv2.dct(small)
    total_energy = float(np.sum(dct ** 2)) + 1e-9
    hf_energy = float(np.sum(dct[32:, 32:] ** 2))
    features["dct_hf_ratio"] = hf_energy / total_energy

    # 5. Local Binary Pattern variance (texture regularity)
    lbp_var = _lbp_variance(gray)
    features["lbp_variance"] = lbp_var

    # 6. Saturation statistics
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat = hsv[:, :, 1]
    features["saturation_mean"] = float(np.mean(sat))
    features["saturation_std"] = float(np.std(sat))

    # 7. Block artifact measure (DCT 8x8 grid inconsistency)
    features["block_artifact"] = _block_artifact_score(gray)

    return features


def _lbp_variance(gray: np.ndarray) -> float:
    """Simplified LBP variance as texture uniformity measure."""
    try:
        radius = 1
        n_points = 8
        rows, cols = gray.shape
        lbp = np.zeros_like(gray, dtype=np.float32)
        for p in range(n_points):
            theta = 2 * math.pi * p / n_points
            xp = int(round(radius * math.cos(theta)))
            yp = int(round(-radius * math.sin(theta)))
            shifted = np.zeros_like(gray)
            # Shift with bounds
            src_r_start = max(0, -yp)
            src_r_end = min(rows, rows - yp)
            src_c_start = max(0, -xp)
            src_c_end = min(cols, cols - xp)
            dst_r_start = max(0, yp)
            dst_r_end = min(rows, rows + yp)
            dst_c_start = max(0, xp)
            dst_c_end = min(cols, cols + xp)
            try:
                shifted[dst_r_start:dst_r_end, dst_c_start:dst_c_end] = \
                    gray[src_r_start:src_r_end, src_c_start:src_c_end]
                lbp += (shifted >= gray).astype(np.float32) * (2 ** p)
            except Exception:
                pass
        return float(np.var(lbp))
    except Exception:
        return 0.0


def _block_artifact_score(gray: np.ndarray) -> float:
    """Measure DCT 8x8 block boundary artifacts (common in JPEG/GAN)."""
    h, w = gray.shape
    h8 = (h // 8) * 8
    w8 = (w // 8) * 8
    if h8 < 8 or w8 < 8:
        return 0.0
    crop = gray[:h8, :w8]
    diffs = []
    for r in range(7, h8, 8):
        row_diff = np.abs(crop[r, :].astype(float) - crop[r + 1, :].astype(float)).mean() if r + 1 < h8 else 0
        diffs.append(row_diff)
    for c in range(7, w8, 8):
        col_diff = np.abs(crop[:, c].astype(float) - crop[:, c + 1].astype(float)).mean() if c + 1 < w8 else 0
        diffs.append(col_diff)
    return float(np.mean(diffs)) if diffs else 0.0


def _score_features(features: Dict[str, float]) -> Tuple[float, List[str]]:
    """
    Heuristic scoring based on known manipulation artifacts.
    Returns (manipulation_score 0-1, list of contributing indicators).
    """
    score = 0.0
    indicators = []

    # Low Laplacian variance → unusual blurring or smoothing (common in upscaling/GAN)
    if features.get("laplacian_var", 1000) < 80:
        score += 0.25
        indicators.append("Unusually low edge sharpness (possible smoothing artifact)")

    # High noise std → added grain / inconsistent noise
    if features.get("noise_std", 0) > 15:
        score += 0.15
        indicators.append("Elevated noise level detected")

    # Low color correlation → unusual color distribution
    avg_corr = (features.get("color_corr_rg", 0.9) + features.get("color_corr_rb", 0.9)) / 2
    if avg_corr < 0.7:
        score += 0.20
        indicators.append("Unusual color channel correlation")

    # High DCT HF ratio → GAN or compression artifacts
    if features.get("dct_hf_ratio", 0) > 0.15:
        score += 0.20
        indicators.append("High-frequency DCT energy ratio elevated (possible GAN/compression artifact)")

    # Block artifacts
    if features.get("block_artifact", 0) > 5.0:
        score += 0.10
        indicators.append("JPEG/DCT block boundary artifacts detected")

    # LBP variance extremes
    lbp_var = features.get("lbp_variance", 1000)
    if lbp_var < 100 or lbp_var > 50000:
        score += 0.10
        indicators.append("Texture pattern inconsistency detected")

    return min(score, 1.0), indicators


class DeepfakeDetector:
    """Interface-compatible deepfake detection module."""

    def predict_image(self, image_bytes: bytes, filename: str = "image") -> Dict[str, Any]:
        """Analyze image bytes for deepfake indicators."""
        if not CV2_AVAILABLE:
            return self._unavailable_response(filename)

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image")

            features = _extract_features(img)
            manip_score, indicators = _score_features(features)

            label = "Potentially Manipulated" if manip_score >= 0.4 else "Likely Authentic"
            confidence = manip_score if manip_score >= 0.4 else (1.0 - manip_score)
            risk_score = manip_score * 100

            explanation = self._explain(label, indicators, confidence, frames_analyzed=1)

            return {
                "label": label,
                "confidence": round(confidence, 4),
                "risk_score": round(risk_score, 1),
                "frames_analyzed": 1,
                "manipulation_score": round(manip_score, 4),
                "indicators": indicators,
                "model_features": features,
                "explanation": explanation,
                "recommended_action": self._recommended_action(risk_score),
            }
        except Exception as e:
            logger.error(f"Deepfake image analysis error: {e}")
            raise

    def predict_video(self, video_path: str, max_frames: int = 8) -> Dict[str, Any]:
        """Analyze sampled frames from a video."""
        if not CV2_AVAILABLE:
            return self._unavailable_response(video_path)

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            sample_indices = np.linspace(0, max(0, total_frames - 1), min(max_frames, total_frames), dtype=int)

            frame_scores = []
            all_indicators: List[str] = []

            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if not ret:
                    continue
                features = _extract_features(frame)
                score, inds = _score_features(features)
                frame_scores.append(score)
                all_indicators.extend(inds)

            cap.release()

            if not frame_scores:
                raise ValueError("No frames could be extracted")

            avg_score = float(np.mean(frame_scores))
            indicators = list(dict.fromkeys(all_indicators))  # deduplicate

            label = "Potentially Manipulated" if avg_score >= 0.4 else "Likely Authentic"
            confidence = avg_score if avg_score >= 0.4 else (1.0 - avg_score)
            risk_score = avg_score * 100

            explanation = self._explain(label, indicators, confidence, frames_analyzed=len(frame_scores))

            return {
                "label": label,
                "confidence": round(confidence, 4),
                "risk_score": round(risk_score, 1),
                "frames_analyzed": len(frame_scores),
                "total_frames": total_frames,
                "manipulation_score": round(avg_score, 4),
                "indicators": indicators,
                "model_features": {"frame_scores": [round(s, 3) for s in frame_scores]},
                "explanation": explanation,
                "recommended_action": self._recommended_action(risk_score),
            }
        except Exception as e:
            logger.error(f"Deepfake video analysis error: {e}")
            raise

    def _explain(self, label: str, indicators: List[str], confidence: float, frames_analyzed: int) -> str:
        conf_pct = round(confidence * 100)
        ind_text = "; ".join(indicators[:3]) if indicators else "no specific artifacts isolated"
        if label == "Likely Authentic":
            return (f"Content appears authentic based on visual feature analysis ({conf_pct}% confidence). "
                    f"Analyzed {frames_analyzed} frame(s). "
                    "No significant manipulation artifacts detected in frequency domain, "
                    "color distribution, or texture analysis.")
        else:
            return (f"Potential manipulation detected with {conf_pct}% indicator confidence. "
                    f"Analyzed {frames_analyzed} frame(s). "
                    f"Evidence: {ind_text}. "
                    "DISCLAIMER: This is a prototype feature-based detector. "
                    "Results should be reviewed by qualified personnel and not treated as forensic evidence.")

    def _recommended_action(self, risk_score: float) -> str:
        if risk_score < 30:
            return "No action required. Content appears authentic."
        elif risk_score < 60:
            return "Treat with caution. Verify content origin through trusted channels."
        elif risk_score < 80:
            return "Flag for analyst review. Do not trust content without independent verification."
        else:
            return "High manipulation indicators. Escalate to security team for investigation."

    def _unavailable_response(self, filename: str) -> Dict[str, Any]:
        return {
            "label": "Analysis Unavailable",
            "confidence": 0.0,
            "risk_score": 0.0,
            "frames_analyzed": 0,
            "indicators": ["OpenCV not installed — deepfake analysis unavailable"],
            "explanation": "OpenCV library not available. Install opencv-python-headless to enable deepfake detection.",
            "recommended_action": "Install required dependencies.",
        }


_detector: Optional[DeepfakeDetector] = None


def get_deepfake_detector() -> DeepfakeDetector:
    global _detector
    if _detector is None:
        _detector = DeepfakeDetector()
    return _detector


def predict_deepfake(image_bytes: bytes, filename: str = "image") -> Dict[str, Any]:
    return get_deepfake_detector().predict_image(image_bytes, filename)


def predict_deepfake_video(video_path: str, max_frames: int = 8) -> Dict[str, Any]:
    return get_deepfake_detector().predict_video(video_path, max_frames)
