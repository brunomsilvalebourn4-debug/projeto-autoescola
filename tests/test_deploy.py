import tempfile
import unittest
from pathlib import Path

from app import create_app


class DeployTest(unittest.TestCase):
    def test_health_confirma_aplicacao_e_banco(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(
                {
                    "TESTING": True,
                    "DB_NAME": str(Path(directory) / "health.db"),
                    "SECRET_KEY": "teste",
                }
            )
            response = app.test_client().get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"database": "ok", "status": "ok"})

    def test_producao_recusa_chave_padrao(self):
        with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
            create_app({"APP_ENV": "production", "SECRET_KEY": "dev-change-me"})

    def test_blueprint_de_deploy_nao_contem_segredo(self):
        blueprint = (Path(__file__).resolve().parent.parent / "render.yaml").read_text(encoding="utf-8")
        self.assertIn("generateValue: true", blueprint)
        self.assertIn("DATABASE_PATH", blueprint)
        self.assertIn("/var/data/autoescola.db", blueprint)
        self.assertIn("healthCheckPath: /health", blueprint)
        self.assertNotIn("troque-por-uma-chave", blueprint)


if __name__ == "__main__":
    unittest.main()
