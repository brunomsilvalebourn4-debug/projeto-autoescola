"""Cria o administrador inicial em ambientes efêmeros de demonstração."""

import os
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config  # noqa: E402


SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def required_environment(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Defina a variável de ambiente {name}.")
    return value


def main():
    name = os.environ.get("INITIAL_ADMIN_NAME", "Administrador").strip() or "Administrador"
    email = required_environment("INITIAL_ADMIN_EMAIL").lower()
    password = required_environment("INITIAL_ADMIN_PASSWORD")

    if "@" not in email:
        raise SystemExit("INITIAL_ADMIN_EMAIL precisa conter um e-mail válido.")
    if len(password) < 8:
        raise SystemExit("INITIAL_ADMIN_PASSWORD precisa ter pelo menos 8 caracteres.")

    database_path = Path(Config.DB_NAME)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            connection.execute(
                "INSERT INTO users (nome, email, senha_hash, perfil) VALUES (?, ?, ?, 'ADMINISTRADOR')",
                (name, email, generate_password_hash(password)),
            )
            connection.commit()
            print("Administrador inicial criado.")
        else:
            print("Banco já possui usuário; nenhuma credencial foi alterada.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
