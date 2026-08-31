import tempfile
import unittest
from pathlib import Path


class PythonAnywhereWsgiTest(unittest.TestCase):
    def test_configuracao_persiste_chave_e_banco_fora_do_repositorio(self):
        source = (Path(__file__).resolve().parent.parent / "pythonanywhere_wsgi.py").read_text(encoding="utf-8")

        self.assertIn('Path.home() / ".local" / "share" / "autoescola"', source)
        self.assertIn('os.environ.setdefault("APP_ENV", "production")', source)
        self.assertIn('os.environ.setdefault("DATABASE_PATH"', source)
        self.assertIn('os.environ.setdefault("SESSION_COOKIE_SECURE", "true")', source)
        self.assertNotIn("dev-change-me", source)

    def test_chave_gerada_tem_entropia_suficiente(self):
        import secrets

        with tempfile.TemporaryDirectory() as directory:
            secret_file = Path(directory) / "secret_key"
            secret_file.write_text(secrets.token_urlsafe(64), encoding="utf-8")
            self.assertGreaterEqual(len(secret_file.read_text(encoding="utf-8")), 80)


if __name__ == "__main__":
    unittest.main()
