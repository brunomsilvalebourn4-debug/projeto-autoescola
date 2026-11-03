import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    APP_NAME = "Sistema de Gestão de Autoescola"
    APP_ENV = os.environ.get("APP_ENV", "development").lower()
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    DB_NAME = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database.db"))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = True
    CSRF_ENABLED = True
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "America/Sao_Paulo")
    ALUNO_APP_TOKEN_DIAS = int(os.environ.get("ALUNO_APP_TOKEN_DIAS", "30"))
    ALUNO_APP_EXIGIR_HTTPS = os.environ.get("ALUNO_APP_EXIGIR_HTTPS", "true" if APP_ENV == "production" else "false").lower() == "true"
    # Quantidade de proxies reversos confiáveis à frente da aplicação (Render e PythonAnywhere usam 1).
    ALUNO_APP_PROXIES = int(os.environ.get("ALUNO_APP_PROXIES", "1" if APP_ENV == "production" else "0"))
