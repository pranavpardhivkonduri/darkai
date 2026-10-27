"""
Phishing / Malicious Text Detector
====================================
Uses TF-IDF + Logistic Regression trained on a built-in labelled dataset.
The training set is composed of representative phishing patterns and
legitimate text patterns. On first import the model is trained and
cached in memory (< 1 second on a laptop). No external dataset download
is needed — the model works out-of-the-box.

Limitations (documented):
- Training data is a curated demonstration set (~200 samples).
- Intended for academic prototype demonstration, not production.
- Replace TRAINING_DATA below with a real dataset (e.g. Enron + SpamAssassin)
  to improve real-world accuracy.
"""

import re
import json
import logging
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

# ─── Training Data ─────────────────────────────────────────────────────────
# Label: 0 = Legitimate, 1 = Suspicious, 2 = Phishing
TRAINING_DATA: List[Tuple[str, int]] = [
    # Phishing samples (label=2)
    ("URGENT: Your account has been compromised. Click here immediately to verify your credentials http://secure-login-verify.xyz/account", 2),
    ("Dear Customer, your PayPal account is suspended. Login now at http://paypal-secure.ru/login to restore access.", 2),
    ("You have won a $1000 Amazon gift card! Claim your prize now before it expires. Click: http://amaz0n-rewards.com/claim", 2),
    ("ALERT: Unusual sign-in activity detected on your Microsoft account. Verify your identity immediately or your account will be locked.", 2),
    ("Your bank account has been locked due to suspicious activity. Provide your SSN and password to unlock: http://bank-secure.net/unlock", 2),
    ("Congratulations! You are our lucky winner. Send your credit card details to claim $5000 prize money.", 2),
    ("Action Required: Your Apple ID has been disabled. Verify your billing information to reactivate it immediately.", 2),
    ("IRS NOTICE: You owe back taxes. Pay immediately using iTunes gift cards to avoid arrest. Call 1-800-555-FAKE.", 2),
    ("Your Netflix subscription has expired. Update payment details now: http://netflix-billing-update.com/pay", 2),
    ("SECURITY ALERT: Someone logged into your Gmail from Nigeria. Change your password immediately: http://google-security.tk/reset", 2),
    ("Dear user, confirm your email address or your account will be deleted within 24 hours. Click here to verify.", 2),
    ("Your package could not be delivered. Provide credit card to pay shipping fee: http://fedex-delivery.xyz/pay", 2),
    ("WARNING: Your computer has been infected with a virus. Call our toll-free number immediately for support.", 2),
    ("You have an unclaimed inheritance of $2.5 million. Send $500 processing fee to receive funds.", 2),
    ("Verify your identity now or lose access to your account permanently. SSN and password required.", 2),
    ("FINAL NOTICE: Your subscription ends today. Update billing at paypal-account-verify.com to continue service.", 2),
    ("Your account will be suspended in 2 hours. Login here to confirm your identity: http://suspicious-login.net", 2),
    ("Enter your credit card details to claim free iPhone 15. Limited time offer: http://free-iphone.xyz", 2),
    ("Your Venmo account shows unauthorized transaction of $499. Dispute here: http://venmo-security.fake/dispute", 2),
    ("Urgent: Your social security number has been suspended. Call immediately to avoid legal consequences.", 2),
    ("Click here to verify your account http://bit.ly/3xFakeLink or it will be permanently deleted", 2),
    ("Dear valued customer please update your banking credentials using this secure link http://1st-bank-login.ru", 2),
    ("You are selected for a COVID-19 relief fund. Submit your bank details to receive $3200 stimulus payment.", 2),
    ("Your email password expires in 24 hours. Update now at http://webmail-secure.info/update", 2),
    ("HR Department: Your salary has been updated. Verify your direct deposit information immediately.", 2),

    # Suspicious samples (label=1)
    ("Hello, I came across your profile and would like to discuss a business opportunity that could benefit you.", 1),
    ("Exclusive offer for selected customers only. Reply to learn more about our special investment program.", 1),
    ("Your account shows unusual activity. Please review recent transactions and contact support if needed.", 1),
    ("You may qualify for a special discount. Provide your contact information to receive details.", 1),
    ("Limited time offer - 90% off all products. Today only. Claim your discount now.", 1),
    ("Someone is trying to access your account from a new device. If this was not you, click to secure account.", 1),
    ("Your recent order has been delayed. Track your shipment and update delivery preferences.", 1),
    ("Congratulations on being pre-approved for a $50,000 loan with 0% interest for 6 months.", 1),
    ("Your payment of $299 was declined. Update your payment method to avoid service interruption.", 1),
    ("We noticed you haven't logged in recently. Click to verify your account is still active.", 1),
    ("Free trial ending soon. Upgrade now to avoid losing your data and preferences.", 1),
    ("Your resume was viewed by 15 recruiters this week. See who's interested in your profile.", 1),
    ("You've earned cashback rewards. Redeem before they expire on the 31st.", 1),

    # Legitimate samples (label=0)
    ("Hi John, just following up on our meeting from yesterday. Let me know if you have any questions.", 0),
    ("Your monthly statement is ready to view in your online banking portal.", 0),
    ("Thanks for your order! Your item will ship within 2-3 business days.", 0),
    ("Meeting reminder: Team standup tomorrow at 10 AM in Conference Room B.", 0),
    ("Your password was successfully changed. If you did not make this change, contact support.", 0),
    ("Welcome to the team! Your account has been created. Please set your password using the link sent separately.", 0),
    ("Here are the action items from today's meeting: 1. Review proposal 2. Send feedback by Friday.", 0),
    ("Your subscription renewal is coming up on October 15. No action needed unless you wish to cancel.", 0),
    ("Thank you for contacting support. We will respond within 1-2 business days.", 0),
    ("Quarterly report is attached for your review. Please share any feedback before Monday.", 0),
    ("Your Amazon order #123-456-789 has shipped. Estimated delivery: Oct 5-7.", 0),
    ("Hi, I wanted to share this interesting article about machine learning I came across today.", 0),
    ("Please review the attached document and provide your signature by end of week.", 0),
    ("The project deadline has been moved to November 1st. Please update your schedules accordingly.", 0),
    ("Your appointment is confirmed for Tuesday at 2:30 PM. Please arrive 10 minutes early.", 0),
    ("Thank you for your donation! Your contribution makes a real difference.", 0),
    ("Happy birthday! Wishing you a wonderful day filled with joy.", 0),
    ("Your flight confirmation: AA1234, departing Oct 10 at 8:45 AM from JFK to LAX.", 0),
    ("The gym will be closed for maintenance on Saturday from 8 AM to 2 PM.", 0),
    ("Please find the updated project timeline in the shared Google Drive folder.", 0),
    ("Reminder: Your annual physical is scheduled for next Wednesday at 9 AM.", 0),
    ("We'd love to hear your feedback about your recent experience with our service.", 0),
    ("Your tax return has been processed and a refund of $432 will be deposited within 21 days.", 0),
    ("Good news - your loan application has been approved! A representative will contact you.", 0),
    ("Can we reschedule our call to Thursday? I have a conflict on Wednesday afternoon.", 0),
    ("The new version of the software is now available. Update when convenient.", 0),
    ("Your child did great at school today! Here's a summary of classroom activities.", 0),
    ("Friendly reminder: library books are due back this Friday.", 0),
    ("Team lunch on Friday at noon - pizza is on the company this week!", 0),
    ("Your recent purchase was successful. Receipt attached for your records.", 0),
]

# ─── URL Feature Extraction ────────────────────────────────────────────────
SUSPICIOUS_TLD = {".xyz", ".tk", ".ml", ".cf", ".ga", ".ru", ".cn", ".pw", ".top", ".info", ".link", ".click"}
PHISHING_KEYWORDS = [
    "verify", "confirm", "update", "secure", "login", "signin", "account", "suspend",
    "locked", "urgent", "immediately", "credential", "password", "ssn", "social-security",
    "paypal", "ebay", "amazon", "apple", "microsoft", "google", "netflix", "irs",
    "bank", "credit", "billing", "payment", "reward", "prize", "winner", "claim",
    "gift-card", "free", "discount", "expire", "act-now", "click-here", "limited",
]


def extract_url_features(url: str) -> Dict[str, Any]:
    """Extract structural features from a URL without visiting it."""
    features = {
        "has_ip": False,
        "url_length": len(url),
        "num_subdomains": 0,
        "has_suspicious_tld": False,
        "has_phishing_keyword": False,
        "num_special_chars": 0,
        "has_https": url.startswith("https://"),
        "has_at_symbol": "@" in url,
        "has_double_slash": "//" in url[8:] if len(url) > 8 else False,
        "num_dots": url.count("."),
        "suspicious_tld": None,
        "matched_keywords": [],
    }

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # IP address instead of domain
        ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        features["has_ip"] = bool(ip_pattern.match(hostname))

        # Subdomains
        parts = hostname.split(".")
        features["num_subdomains"] = max(0, len(parts) - 2)

        # TLD
        if parts:
            tld = "." + parts[-1].lower()
            features["has_suspicious_tld"] = tld in SUSPICIOUS_TLD
            features["suspicious_tld"] = tld

        # Keywords in full URL
        url_lower = url.lower()
        matched = [kw for kw in PHISHING_KEYWORDS if kw in url_lower]
        features["has_phishing_keyword"] = len(matched) > 0
        features["matched_keywords"] = matched

        # Special chars
        features["num_special_chars"] = sum(url.count(c) for c in "-_=&%~")

    except Exception:
        pass

    return features


def _compute_url_risk(url_features: Dict[str, Any]) -> float:
    """Heuristic URL risk score 0-100."""
    score = 0.0
    if url_features.get("has_ip"):
        score += 30
    if url_features.get("has_suspicious_tld"):
        score += 20
    if url_features.get("has_phishing_keyword"):
        score += 20
    if not url_features.get("has_https"):
        score += 10
    if url_features.get("url_length", 0) > 75:
        score += 10
    if url_features.get("num_subdomains", 0) > 2:
        score += 15
    if url_features.get("has_at_symbol"):
        score += 20
    if url_features.get("num_special_chars", 0) > 5:
        score += 5
    return min(score, 100.0)


# ─── Model ──────────────────────────────────────────────────────────────────
class PhishingDetector:
    def __init__(self):
        self._pipeline: Pipeline | None = None
        self._classes = ["Legitimate", "Suspicious", "Phishing"]
        self._train()

    def _train(self):
        texts, labels = zip(*TRAINING_DATA)
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
                stop_words="english",
            )),
            ("clf", LogisticRegression(
                C=1.0,
                max_iter=500,
                class_weight="balanced",
                random_state=42,
            )),
        ])
        self._pipeline.fit(X_train, y_train)
        y_pred = self._pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, target_names=self._classes, output_dict=True)
        logger.info(
            "Phishing detector trained | "
            f"Accuracy: {report.get('accuracy', 0):.2f} | "
            f"Macro-F1: {report.get('macro avg', {}).get('f1-score', 0):.2f}"
        )
        self._eval_report = report

    def predict(self, text: str, url: str = "") -> Dict[str, Any]:
        """
        Run the phishing classifier and optionally augment with URL features.
        Returns detection result, confidence, risk score, indicators and XAI explanation.
        """
        if not text.strip() and not url.strip():
            raise ValueError("Both text and url are empty")

        combined = text
        url_features: Dict[str, Any] = {}
        url_risk = 0.0

        if url:
            url_features = extract_url_features(url)
            url_risk = _compute_url_risk(url_features)
            combined = f"{text} {url}"

        probs = self._pipeline.predict_proba([combined])[0]
        pred_class = int(np.argmax(probs))
        confidence = float(np.max(probs))

        # Merge URL risk into confidence for phishing
        if url_risk > 50 and pred_class < 2:
            pred_class = 2
            confidence = max(confidence, url_risk / 100)

        label = self._classes[pred_class]

        # Indicators
        indicators = self._extract_indicators(text, url_features)

        # Risk score
        risk_score = self._compute_risk(pred_class, confidence, url_risk, indicators)

        # XAI explanation
        explanation = self._explain(label, indicators, url_features, confidence)

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "risk_score": round(risk_score, 1),
            "threat_class": pred_class,
            "indicators": indicators,
            "url_features": url_features,
            "explanation": explanation,
            "class_probabilities": {
                self._classes[i]: round(float(p), 4) for i, p in enumerate(probs)
            },
        }

    def _extract_indicators(self, text: str, url_features: Dict[str, Any]) -> List[str]:
        indicators = []
        text_lower = text.lower()

        # Urgency
        urgency_words = ["urgent", "immediately", "now", "asap", "act now", "limited time", "expires", "deadline", "24 hours"]
        if any(w in text_lower for w in urgency_words):
            indicators.append("Urgent language detected")

        # Credential request
        cred_words = ["password", "username", "login", "credential", "verify", "confirm", "ssn", "social security"]
        if any(w in text_lower for w in cred_words):
            indicators.append("Credential request detected")

        # Financial request
        fin_words = ["credit card", "bank account", "wire transfer", "bitcoin", "gift card", "itunes", "payment", "billing"]
        if any(w in text_lower for w in fin_words):
            indicators.append("Financial information request")

        # Prize/reward
        prize_words = ["won", "winner", "prize", "reward", "congratulations", "selected", "lucky"]
        if any(w in text_lower for w in prize_words):
            indicators.append("Prize/reward claim (common social engineering tactic)")

        # Impersonation
        impersonation = ["paypal", "amazon", "apple", "microsoft", "google", "netflix", "irs", "fbi", "cdc", "fedex", "ups"]
        matched = [b for b in impersonation if b in text_lower]
        if matched:
            indicators.append(f"Brand impersonation: {', '.join(matched)}")

        # Suspicious URL
        if url_features.get("has_suspicious_tld"):
            indicators.append(f"Suspicious domain extension: {url_features.get('suspicious_tld')}")
        if url_features.get("has_ip"):
            indicators.append("URL uses raw IP address instead of domain name")
        if url_features.get("matched_keywords"):
            indicators.append(f"Phishing keywords in URL: {', '.join(url_features['matched_keywords'][:3])}")
        if not url_features.get("has_https") and url_features:
            indicators.append("URL does not use HTTPS")

        # Threat language
        threat_words = ["arrest", "lawsuit", "legal action", "penalty", "suspend", "locked", "disabled"]
        if any(w in text_lower for w in threat_words):
            indicators.append("Threatening language (account suspension / legal threat)")

        return indicators

    def _compute_risk(self, pred_class: int, confidence: float, url_risk: float, indicators: List[str]) -> float:
        base = {0: 5, 1: 40, 2: 70}[pred_class]
        bonus = min(confidence * 20, 20) + min(len(indicators) * 3, 15)
        url_component = url_risk * 0.2
        return min(base + bonus + url_component, 100.0)

    def _explain(self, label: str, indicators: List[str], url_features: Dict[str, Any], confidence: float) -> str:
        if label == "Legitimate":
            return ("The content does not exhibit common phishing characteristics. "
                    "No significant urgency indicators, credential requests, or suspicious URL patterns detected.")

        ind_text = "; ".join(indicators[:4]) if indicators else "general suspicious patterns"
        conf_pct = round(confidence * 100)

        if label == "Phishing":
            return (f"Content classified as PHISHING with {conf_pct}% model confidence. "
                    f"Detected indicators: {ind_text}. "
                    "These patterns are strongly associated with phishing attacks designed to steal "
                    "credentials or financial information through social engineering.")
        else:
            return (f"Content is SUSPICIOUS with {conf_pct}% model confidence. "
                    f"Detected: {ind_text}. "
                    "Review carefully before taking any action requested in this message.")

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "TF-IDF + Logistic Regression",
            "training_samples": len(TRAINING_DATA),
            "classes": self._classes,
            "evaluation": self._eval_report,
            "note": "Prototype dataset. Replace TRAINING_DATA with real phishing corpus for production use.",
        }


# Singleton
_detector: PhishingDetector | None = None


def get_phishing_detector() -> PhishingDetector:
    global _detector
    if _detector is None:
        _detector = PhishingDetector()
    return _detector


def predict_phishing(text: str, url: str = "") -> Dict[str, Any]:
    """Public interface — predict phishing on text/URL."""
    return get_phishing_detector().predict(text, url)
