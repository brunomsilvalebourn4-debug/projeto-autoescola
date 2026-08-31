"""Ponto de entrada WSGI para hospedagem no PythonAnywhere."""

import os
import secrets
from pathlib import Path


DATA_DIR = Path.home() / ".local" / "share" / "autoescola"
SECRET_FILE = DATA_DIR / "secret_key"


def configure_environment():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_urlsafe(64), encoding="utf-8")
        try:
            SECRET_FILE.chmod(0o600)
        except OSError:
            pass

    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("DATABASE_PATH", str(DATA_DIR / "autoescola.db"))
    os.environ.setdefault("SECRET_KEY", SECRET_FILE.read_text(encoding="utf-8").strip())
    os.environ.setdefault("SESSION_COOKIE_SECURE", "true")
    os.environ.setdefault("FLASK_DEBUG", "false")


configure_environment()

from app import app as application  # noqa: E402

