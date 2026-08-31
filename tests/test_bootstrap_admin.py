import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import check_password_hash


class BootstrapAdminTest(unittest.TestCase):
    def test_cria_admin_uma_unica_vez_sem_expor_senha(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.db"
            environment = os.environ.copy()
            environment.update(
                {
                    "DATABASE_PATH": str(database),
                    "INITIAL_ADMIN_NAME": "Admin Demo",
                    "INITIAL_ADMIN_EMAIL": "admin@demo.test",
                    "INITIAL_ADMIN_PASSWORD": "senha-segura-123",
                }
            )
            script = Path(__file__).resolve().parent.parent / "scripts" / "bootstrap_admin.py"
            first = subprocess.run([sys.executable, str(script)], env=environment, capture_output=True, text=True)
            second = subprocess.run([sys.executable, str(script)], env=environment, capture_output=True, text=True)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotIn("senha-segura-123", first.stdout + first.stderr)
            connection = sqlite3.connect(database)
            user = connection.execute("SELECT email, senha_hash, perfil FROM users").fetchone()
            total = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            connection.close()

        self.assertEqual(total, 1)
        self.assertEqual(user[0], "admin@demo.test")
        self.assertTrue(check_password_hash(user[1], "senha-segura-123"))
        self.assertEqual(user[2], "ADMINISTRADOR")


if __name__ == "__main__":
    unittest.main()
