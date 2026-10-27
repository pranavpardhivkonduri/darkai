"""
DarkAI Backend Integration Tests
Tests all major API endpoints and ML modules.
Run with: venv\Scripts\pytest tests/ -v
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite:///./test_darkai.db"

import os
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32chars-long"

from app.main import app
from app.database.db import Base, get_db
from app.database.db import engine as prod_engine

# Create test engine
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    import os
    if os.path.exists("test_darkai.db"):
        try:
            os.remove("test_darkai.db")
        except PermissionError:
            pass


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    # Register admin user
    client.post("/api/v1/auth/register", json={
        "username": "testadmin",
        "email": "testadmin@test.com",
        "password": "TestAdmin@1234",
        "role": "ADMIN",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "TestAdmin@1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert not data["requires_mfa"]
    return data["access_token"]


@pytest.fixture(scope="session")
def analyst_token(client):
    client.post("/api/v1/auth/register", json={
        "username": "testanalyst",
        "email": "testanalyst@test.com",
        "password": "TestAnalyst@1234",
        "role": "ANALYST",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "testanalyst",
        "password": "TestAnalyst@1234",
    })
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def user_token(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "testuser@test.com",
        "password": "TestUser@1234",
        "role": "USER",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestUser@1234",
    })
    return resp.json()["access_token"]


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


# ─── Auth Tests ─────────────────────────────────────────────
class TestAuth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_register_duplicate_email(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "dup_user", "email": "dup@test.com",
            "password": "Dup@1234", "role": "USER"
        })
        resp = client.post("/api/v1/auth/register", json={
            "username": "dup_user2", "email": "dup@test.com",
            "password": "Dup@1234", "role": "USER"
        })
        assert resp.status_code == 409

    def test_login_invalid_credentials(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "username": "testadmin", "password": "wrongpassword"
        })
        assert resp.status_code == 401

    def test_get_me(self, client, admin_token):
        resp = client.get("/api/v1/auth/me", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["username"] == "testadmin"

    def test_unauthorized_access(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)  # No token

# ─── Phishing Analysis Tests ────────────────────────────────
class TestPhishingAnalysis:
    def test_phishing_detected(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/text",
            json={
                "content": "URGENT: Your PayPal account is suspended. Click http://paypal-fake.xyz to restore.",
                "content_type": "email",
            },
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "label" in data
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100
        assert "confidence" in data
        assert "indicators" in data
        assert "explanation" in data
        assert data["threat_type"] == "PHISHING"

    def test_legitimate_email(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/text",
            json={"content": "Hi team, please review the attached report by Friday.", "content_type": "email"},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] in ["Legitimate", "Suspicious", "Phishing"]
        assert data["risk_score"] >= 0

    def test_empty_text_rejected(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/text",
            json={"content": "", "content_type": "email"},
            headers=auth_header(user_token),
        )
        # Should fail — empty input
        assert resp.status_code in [400, 422, 500]

    def test_url_analysis(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/url",
            json={"url": "http://paypal-secure-login.xyz/account"},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_score" in data


# ─── Behavior Analysis Tests ────────────────────────────────
class TestBehaviorAnalysis:
    def test_normal_behavior(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/behavior",
            json={
                "login_hour": 10,
                "failed_attempts": 0,
                "is_new_device": False,
                "is_unusual_location": False,
                "access_frequency": 5.0,
                "session_duration_minutes": 45.0,
                "requests_per_minute": 2.0,
            },
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] in ["Normal", "Anomalous"]
        assert 0 <= data["risk_score"] <= 100

    def test_anomalous_behavior(self, client, user_token):
        resp = client.post(
            "/api/v1/analyze/behavior",
            json={
                "login_hour": 3,
                "failed_attempts": 5,
                "is_new_device": True,
                "is_unusual_location": True,
                "access_frequency": 50.0,
                "session_duration_minutes": 5.0,
                "requests_per_minute": 30.0,
            },
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_score"] > 30  # Should be elevated
        assert len(data["indicators"]) > 0


# ─── Risk Engine Tests ───────────────────────────────────────
class TestRiskEngine:
    def test_calculate_risk(self):
        from app.services.risk_engine import calculate_risk
        result = calculate_risk(phishing_score=90, deepfake_score=0, anomaly_score=0)
        assert result["overall_score"] > 0
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_critical_risk_level(self):
        from app.services.risk_engine import calculate_risk
        result = calculate_risk(phishing_score=100, deepfake_score=100, voice_score=100, anomaly_score=100, auth_risk=100)
        assert result["risk_level"] == "CRITICAL"
        assert result["overall_score"] >= 80

    def test_low_risk_level(self):
        from app.services.risk_engine import calculate_risk
        result = calculate_risk(phishing_score=0, deepfake_score=0, anomaly_score=0)
        assert result["risk_level"] == "LOW"
        assert result["overall_score"] < 30


# ─── Watermark Tests ─────────────────────────────────────────
class TestWatermark:
    def test_create_and_verify_authentic(self, client, user_token):
        import io
        content = b"Test content for watermark verification"
        # Create
        resp = client.post(
            "/api/v1/watermark/create",
            data={"owner": "Test User", "content_id": "TEST-001"},
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "content_hash" in data

        # Verify same content
        resp2 = client.post(
            "/api/v1/watermark/verify",
            data={"content_id": "TEST-001"},
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
            headers=auth_header(user_token),
        )
        assert resp2.status_code == 200
        v = resp2.json()
        assert v["is_authentic"] is True
        assert v["match"] is True

    def test_verify_modified_content(self, client, user_token):
        import io
        # Verify with DIFFERENT content
        resp = client.post(
            "/api/v1/watermark/verify",
            data={"content_id": "TEST-001"},
            files={"file": ("test.txt", io.BytesIO(b"MODIFIED CONTENT"), "text/plain")},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 200
        v = resp.json()
        assert v["is_authentic"] is False
        assert v["match"] is False

    def test_duplicate_content_id_rejected(self, client, user_token):
        import io
        resp = client.post(
            "/api/v1/watermark/create",
            data={"owner": "Owner 2", "content_id": "TEST-001"},
            files={"file": ("test2.txt", io.BytesIO(b"another content"), "text/plain")},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 409


# ─── Audit Chain Tests ───────────────────────────────────────
class TestAuditChain:
    def test_audit_chain_valid(self, client, analyst_token):
        resp = client.post(
            "/api/v1/audit/verify",
            headers=auth_header(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert "VALID" in data["message"]

    def test_audit_logs_accessible(self, client, analyst_token):
        resp = client.get("/api/v1/audit/logs", headers=auth_header(analyst_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_audit_logs_require_analyst(self, client, user_token):
        resp = client.get("/api/v1/audit/logs", headers=auth_header(user_token))
        assert resp.status_code == 403


# ─── Incident Tests ──────────────────────────────────────────
class TestIncidents:
    def test_list_incidents(self, client, user_token):
        resp = client.get("/api/v1/incidents", headers=auth_header(user_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_analyst_can_update_status(self, client, analyst_token, user_token):
        # First create an incident via phishing analysis
        analysis_resp = client.post(
            "/api/v1/analyze/text",
            json={"content": "URGENT: Your account will be deleted! Click verify.xyz/reset now!", "content_type": "email"},
            headers=auth_header(user_token),
        )
        assert analysis_resp.status_code == 200

        # Check if incident was created
        incidents_resp = client.get("/api/v1/incidents", headers=auth_header(analyst_token))
        incidents = incidents_resp.json()
        if incidents:
            inc_id = incidents[0]["id"]
            update_resp = client.post(
                f"/api/v1/incidents/{inc_id}/status",
                json={"status": "INVESTIGATING", "analyst_notes": "Reviewed by test analyst"},
                headers=auth_header(analyst_token),
            )
            assert update_resp.status_code == 200
            assert update_resp.json()["status"] == "INVESTIGATING"

    def test_user_cannot_update_status(self, client, user_token):
        incidents_resp = client.get("/api/v1/incidents", headers=auth_header(user_token))
        incidents = incidents_resp.json()
        if incidents:
            inc_id = incidents[0]["id"]
            resp = client.post(
                f"/api/v1/incidents/{inc_id}/status",
                json={"status": "RESOLVED"},
                headers=auth_header(user_token),
            )
            assert resp.status_code == 403


# ─── Dashboard Tests ─────────────────────────────────────────
class TestDashboard:
    def test_statistics(self, client, user_token):
        resp = client.get("/api/v1/dashboard/statistics", headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_analyses" in data
        assert "threats_detected" in data
        assert "overall_risk_level" in data

    def test_timeline(self, client, user_token):
        resp = client.get("/api/v1/dashboard/timeline?days=7", headers=auth_header(user_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 7


# ─── File Validation Tests ───────────────────────────────────
class TestFileValidation:
    def test_invalid_extension_rejected(self, client, user_token):
        import io
        resp = client.post(
            "/api/v1/analyze/image",
            files={"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 400

    def test_invalid_audio_extension(self, client, user_token):
        import io
        resp = client.post(
            "/api/v1/analyze/audio",
            files={"file": ("shell.php", io.BytesIO(b"<?php echo 'test'; ?>"), "text/php")},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 400


# ─── ML Module Unit Tests ────────────────────────────────────
class TestMLModules:
    def test_phishing_detector_loaded(self):
        from app.services.ml.phishing_detector import get_phishing_detector
        detector = get_phishing_detector()
        assert detector is not None

    def test_phishing_predict(self):
        from app.services.ml.phishing_detector import predict_phishing
        result = predict_phishing("Click here to win $1000! Your account expires in 24 hours.")
        assert "label" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_anomaly_detector_loaded(self):
        from app.services.ml.anomaly_detector import get_behavior_detector
        detector = get_behavior_detector()
        assert detector is not None

    def test_anomaly_detect(self):
        from app.services.ml.anomaly_detector import detect_anomaly
        result = detect_anomaly(login_hour=10, failed_attempts=0)
        assert "label" in result
        assert result["label"] in ["Normal", "Anomalous"]

    def test_audit_hash_chain_compute(self):
        from app.models.audit_models import AuditLog
        h1 = AuditLog.compute_hash(
            sequence=1, event_type="TEST", user_id="uid1",
            analysis_id="", risk_score=0.0, result_label="test",
            details="{}", previous_hash="0" * 64, created_at="2024-01-01T00:00:00"
        )
        h2 = AuditLog.compute_hash(
            sequence=1, event_type="TEST", user_id="uid1",
            analysis_id="", risk_score=0.0, result_label="test",
            details="{}", previous_hash="0" * 64, created_at="2024-01-01T00:00:00"
        )
        assert h1 == h2  # Deterministic
        assert len(h1) == 64  # SHA-256 hex

    def test_watermark_hash_deterministic(self):
        from app.services.watermark_service import compute_content_hash
        content = b"test content"
        h1 = compute_content_hash(content)
        h2 = compute_content_hash(content)
        assert h1 == h2
        assert len(h1) == 64

    def test_watermark_hash_different_content(self):
        from app.services.watermark_service import compute_content_hash
        assert compute_content_hash(b"content a") != compute_content_hash(b"content b")
