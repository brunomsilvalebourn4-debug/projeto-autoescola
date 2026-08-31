import sqlite3
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import create_app
from scripts.generate_dev_data import gerar_banco
from services.disponibilidade_service import sugerir_instrutores


class CargaTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "carga.db")
        self.totais = gerar_banco(self.db)
        self.app = create_app({"TESTING": True, "DB_NAME": self.db, "SECRET_KEY": "carga"})
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session.update(user_id=1, usuario="Carga", perfil="ADMINISTRADOR")

    def tearDown(self):
        self.temp.cleanup()

    def medir(self, operacao, limite=2.0):
        inicio = time.perf_counter()
        resultado = operacao()
        duracao = time.perf_counter() - inicio
        self.assertLess(duracao, limite, f"Operação demorou {duracao:.3f}s")
        return resultado

    def test_quantidades_e_integridade(self):
        connection = sqlite3.connect(self.db)
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            for tabela, esperado in self.totais.items():
                nome = "processos_habilitacao" if tabela == "processos" else "etapas_processo" if tabela == "etapas" else tabela
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {nome}").fetchone()[0], esperado)
        finally:
            connection.close()

    def test_pesquisa_dashboard_calendario_relatorios(self):
        self.assertEqual(self.medir(lambda: self.client.get("/alunos?q=Aluno+Teste+050")).status_code, 200)
        self.assertEqual(self.medir(lambda: self.client.get("/dashboard")).status_code, 200)
        self.assertEqual(self.medir(lambda: self.client.get(f"/calendario?semana={date.today().isoformat()}")).status_code, 200)
        inicio = (date.today() - timedelta(days=90)).isoformat()
        fim = (date.today() + timedelta(days=90)).isoformat()
        self.assertEqual(self.medir(lambda: self.client.get(f"/relatorios?data_inicio={inicio}&data_fim={fim}")).status_code, 200)

    def test_sugestao_com_centenas_de_aulas(self):
        with self.app.app_context():
            opcoes = self.medir(lambda: sugerir_instrutores("B"))
        self.assertEqual(len(opcoes), 10)
        self.assertTrue(all("horarios_livres" in item for item in opcoes))

    def test_gerador_recusa_banco_real_e_existente(self):
        with self.assertRaises(ValueError):
            gerar_banco(self.app.config.get("REAL_DATABASE_FOR_TEST", str(Path.cwd() / "database.db")))
        with self.assertRaises(FileExistsError):
            gerar_banco(self.db)


if __name__ == "__main__":
    unittest.main()
