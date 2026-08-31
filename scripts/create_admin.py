import argparse
import getpass
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config

SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def main():
    parser = argparse.ArgumentParser(description="Cria o primeiro administrador da Autoescola.")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")
    if len(senha) < 8:
        raise SystemExit("A senha precisa ter pelo menos 8 caracteres.")

    connection = sqlite3.connect(Config.DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO users (nome, email, senha_hash, perfil) VALUES (?, ?, ?, 'ADMINISTRADOR')",
            (args.nome.strip(), args.email.strip().lower(), generate_password_hash(senha)),
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        raise SystemExit(f"Não foi possível criar o administrador: {error}") from error
    finally:
        connection.close()
    print("Administrador criado com sucesso.")


if __name__ == "__main__":
    main()
