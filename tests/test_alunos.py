import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app


class AlunosTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        self.app = create_app({"TESTING": True, "DB_NAME": self.db_path, "SECRET_KEY": "test"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def autenticar(self, perfil="ATENDENTE"):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["usuario"] = "Teste"
            session["perfil"] = perfil

    @staticmethod
    def dados_validos(cpf="52998224725", nome="Maria da Silva"):
        return {
            "nome_completo": nome,
            "cpf": cpf,
            "telefone": "(11) 99999-9999",
            "categoria_cnh": "B",
            "status": "ATIVO",
            "email": "maria@example.com",
            "uf": "SP",
        }

    def test_exige_login_e_perfil(self):
        self.assertEqual(self.client.get("/alunos").status_code, 302)
        self.autenticar("INSTRUTOR")
        self.assertEqual(self.client.get("/alunos").status_code, 403)

    def test_cadastra_visualiza_e_edita_aluno(self):
        self.autenticar()
        response = self.client.post("/alunos/novo", data=self.dados_validos(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Maria da Silva", response.data)

        response = self.client.post(
            "/alunos/1/editar",
            data=self.dados_validos(nome="Maria Souza"),
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Maria Souza", response.data)

    def test_rejeita_cpf_invalido_e_duplicado(self):
        self.autenticar()
        response = self.client.post("/alunos/novo", data=self.dados_validos(cpf="11111111111"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("CPF válido".encode(), response.data)

        self.client.post("/alunos/novo", data=self.dados_validos())
        response = self.client.post("/alunos/novo", data=self.dados_validos(nome="Outra Pessoa"))
        self.assertIn("Já existe um aluno".encode(), response.data)

    def test_pesquisa_filtro_e_paginacao(self):
        self.autenticar()
        connection = sqlite3.connect(self.db_path)
        try:
            for index in range(12):
                connection.execute(
                    "INSERT INTO alunos (nome_completo, cpf, telefone, categoria_cnh, status) VALUES (?, ?, ?, 'B', ?)",
                    (f"Aluno {index:02d}", f"{index:011d}", "11999999999", "ATIVO" if index < 11 else "INATIVO"),
                )
            connection.commit()
        finally:
            connection.close()
        response = self.client.get("/alunos?q=Aluno&status=ATIVO&page=2")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Aluno 10", response.data)
        self.assertNotIn(b"Aluno 11", response.data)

    def test_pesquisa_cpf_formatado(self):
        self.autenticar()
        self.client.post("/alunos/novo", data=self.dados_validos())
        response = self.client.get("/alunos?q=529.982.247-25")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Maria da Silva", response.data)


if __name__ == "__main__":
    unittest.main()
