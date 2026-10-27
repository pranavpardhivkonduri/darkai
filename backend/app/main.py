"""
DarkAI — FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database.db import init_db
from app.api.auth import router as auth_router
from app.api.analysis import router as analysis_router
from app.api.routes import (
    dashboard_router, incident_router, alert_router,
    watermark_router, audit_router, report_router,
)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("darkai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DarkAI starting up...")
    init_db()
    # Pre-warm ML models (loads them into memory once at startup)
    from app.services.ml.phishing_detector import get_phishing_detector
    from app.services.ml.anomaly_detector import get_behavior_detector
    from app.services.ml.deepfake_detector import get_deepfake_detector
    from app.services.ml.voice_detector import get_voice_clone_detector
    get_phishing_detector()
    get_behavior_detector()
    get_deepfake_detector()
    get_voice_clone_detector()
    logger.info("All DarkAI ML models loaded and warm")
    yield
    logger.info("DarkAI shutting down")


app = FastAPI(
    title="DarkAI — Criminal Misuse of AI Detection Platform",
    description=(
        "Academic cybersecurity platform for detecting AI-driven threats: "
        "deepfakes, voice clones, phishing, and behavioral anomalies."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────────
API_PREFIX = f"/api/{settings.API_VERSION}"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(analysis_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(incident_router, prefix=API_PREFIX)
app.include_router(alert_router, prefix=API_PREFIX)
app.include_router(watermark_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)
app.include_router(report_router, prefix=API_PREFIX)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "env": settings.APP_ENV,
    }


@app.get("/")
def root():
    return {
        "message": "DarkAI API is running",
        "docs": "/api/docs",
        "health": "/api/health",
    }
