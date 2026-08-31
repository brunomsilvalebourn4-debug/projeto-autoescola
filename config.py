import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    APP_NAME = "Sistema de Gestão de Autoescola"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DB_NAME = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
