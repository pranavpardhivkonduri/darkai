from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DarkAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./darkai.db"

    # MFA
    MFA_ISSUER: str = "DarkAI-Security"

    # Files
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_IMAGE_EXTENSIONS: str = "jpg,jpeg,png,bmp,webp"
    ALLOWED_AUDIO_EXTENSIONS: str = "wav,mp3,ogg,flac"
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,avi,mov,mkv"

    # Risk thresholds
    RISK_LOW_MAX: int = 29
    RISK_MEDIUM_MAX: int = 59
    RISK_HIGH_MAX: int = 79

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Reports
    REPORTS_DIR: str = "reports"
    MODELS_DIR: str = "../models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    def get_allowed_images(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    def get_allowed_audio(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_AUDIO_EXTENSIONS.split(",")]

    def get_allowed_video(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",")]

    def get_risk_level(self, score: float) -> str:
        if score <= self.RISK_LOW_MAX:
            return "LOW"
        elif score <= self.RISK_MEDIUM_MAX:
            return "MEDIUM"
        elif score <= self.RISK_HIGH_MAX:
            return "HIGH"
        else:
            return "CRITICAL"

    def max_file_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()

# Ensure directories exist
for d in [settings.UPLOAD_DIR, settings.REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
