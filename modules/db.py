import sqlite3
from pathlib import Path

from flask import current_app, g


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


def _configure_connection(connection):
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def get_connection():
    """Retorna uma conexão por contexto de requisição."""
    if "db" not in g:
        g.db = _configure_connection(sqlite3.connect(current_app.config["DB_NAME"]))
    return g.db


def close_connection(_exception=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    """Aplica o esquema idempotente fora das rotas da aplicação."""
    connection = get_connection()
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    connection.commit()


def init_app(app):
    app.teardown_appcontext(close_connection)
    with app.app_context():
        init_db()
