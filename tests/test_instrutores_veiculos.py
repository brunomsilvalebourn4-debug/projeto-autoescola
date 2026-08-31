import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app


class CadastrosTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.db = str(Path(self.tmp.name)/"test.db")
        self.app = create_app({"TESTING": True, "DB_NAME": self.db, "SECRET_KEY": "test"}); self.client = self.app.test_client()
        self.login("ADMINISTRADOR")

    def tearDown(self): self.tmp.cleanup()
    def login(self, perfil):
        with self.client.session_transaction() as s: s.update(user_id=1, usuario="Teste", perfil=perfil)
    def scalar(self, sql):
        connection = sqlite3.connect(self.db)
        try: return connection.execute(sql).fetchone()[0]
        finally: connection.close()

    def instrutor(self, cpf="11144477735"):
        return {"nome":"João Instrutor","cpf":cpf,"telefone":"11999999999","email":"joao@teste.com","horario_inicio":"08:00","horario_fim":"18:00","categorias":["A","B"],"dias":["0","1","2","3","4"],"ativo":"1"}

    def veiculo(self, placa="ABC1D23"):
        return {"placa":placa,"marca":"Fiat","modelo":"Mobi","ano":"2025","categoria":"B","tipo":"Automóvel","status":"DISPONIVEL"}

    def test_crud_instrutor_relacoes_e_status(self):
        r=self.client.post("/instrutores/novo",data=self.instrutor(),follow_redirects=True); self.assertEqual(r.status_code,200); self.assertIn("João Instrutor".encode(),r.data)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM instrutor_categorias"),2); self.assertEqual(self.scalar("SELECT COUNT(*) FROM instrutor_disponibilidade"),5)
        self.client.post("/instrutores/1/alternar-status")
        self.assertEqual(self.scalar("SELECT ativo FROM instrutores"),0)

    def test_instrutor_duplicado_e_horario_invalido(self):
        self.client.post("/instrutores/novo",data=self.instrutor())
        self.assertIn("Já existe".encode(),self.client.post("/instrutores/novo",data=self.instrutor()).data)
        dados=self.instrutor("52998224725"); dados["horario_inicio"]="19:00"; dados["horario_fim"]="08:00"
        self.assertIn("anterior".encode(),self.client.post("/instrutores/novo",data=dados).data)

    def test_crud_veiculo_placa_unica_e_filtros(self):
        r=self.client.post("/veiculos/novo",data=self.veiculo(),follow_redirects=True); self.assertEqual(r.status_code,200); self.assertIn(b"ABC1D23",r.data)
        self.assertIn("Já existe".encode(),self.client.post("/veiculos/novo",data=self.veiculo("abc-1d23")).data)
        self.assertIn(b"ABC1D23",self.client.get("/veiculos?q=Mobi&status=DISPONIVEL&categoria=B").data)
        dados=self.veiculo(); dados["modelo"]="Argo"; self.client.post("/veiculos/1/editar",data=dados)
        self.assertEqual(self.scalar("SELECT modelo FROM veiculos"),"Argo")

    def test_atendente_consulta_mas_nao_altera(self):
        self.login("ATENDENTE")
        self.assertEqual(self.client.get("/instrutores").status_code,200); self.assertEqual(self.client.get("/veiculos").status_code,200)
        self.assertEqual(self.client.get("/instrutores/novo").status_code,403); self.assertEqual(self.client.get("/veiculos/novo").status_code,403)

if __name__ == "__main__": unittest.main()
