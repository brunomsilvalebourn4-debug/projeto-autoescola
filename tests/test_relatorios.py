import sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app
class RelatoriosTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.db=str(Path(self.t.name)/'t.db');self.app=create_app({'TESTING':True,'DB_NAME':self.db,'SECRET_KEY':'x'});self.c=self.app.test_client();con=sqlite3.connect(self.db);con.execute("INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh)VALUES('Ana','1','2','B')");con.commit();con.close()
 def tearDown(self):self.t.cleanup()
 def login(self,perfil):
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil=perfil)
 def test_admin_visualiza_dados_reais(self):
  self.login('ADMINISTRADOR');r=self.c.get('/relatorios?data_inicio=2026-01-01&data_fim=2026-12-31');self.assertEqual(r.status_code,200);self.assertIn(b'Ana',r.data);self.assertIn(b'Alunos ativos (1)',r.data)
 def test_periodo_invalido(self):
  self.login('ADMINISTRADOR');self.assertEqual(self.c.get('/relatorios?data_inicio=2026-12-31&data_fim=2026-01-01').status_code,400)
 def test_atendente_bloqueado(self):
  self.login('ATENDENTE');self.assertEqual(self.c.get('/relatorios').status_code,403)
if __name__=='__main__':unittest.main()
