import sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app
class DashboardTest(unittest.TestCase):
 def test_indicadores_reais(self):
  with tempfile.TemporaryDirectory() as d:
   db=str(Path(d)/'t.db');app=create_app({'TESTING':True,'DB_NAME':db,'SECRET_KEY':'x'});c=sqlite3.connect(db);c.execute("INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh)VALUES('A','1','1','B')");c.execute("INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim)VALUES('I','2','2','08:00','18:00')");c.execute("INSERT INTO veiculos(placa,marca,modelo,categoria,tipo)VALUES('ABC1D23','F','M','B','A')");c.commit();c.close();client=app.test_client()
   with client.session_transaction() as s:s.update(user_id=1,usuario='T',perfil='ADMINISTRADOR')
   r=client.get('/dashboard');self.assertEqual(r.status_code,200);self.assertIn(b'Alunos ativos',r.data);self.assertGreaterEqual(r.data.count(b'>1<'),3)
if __name__=='__main__':unittest.main()
