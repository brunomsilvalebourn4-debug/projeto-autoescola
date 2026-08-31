import sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app

class ProcessosTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=str(Path(self.tmp.name)/'t.db');self.app=create_app({'TESTING':True,'DB_NAME':self.db,'SECRET_KEY':'x'});self.c=self.app.test_client()
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='Teste',perfil='ATENDENTE')
  con=sqlite3.connect(self.db);con.execute("INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh) VALUES('Ana','52998224725','11999999999','B')");con.commit();con.close()
 def tearDown(self):self.tmp.cleanup()
 def scalar(self,sql):
  c=sqlite3.connect(self.db)
  try:return c.execute(sql).fetchone()[0]
  finally:c.close()
 def test_cria_oito_etapas_e_impede_segundo_aberto(self):
  r=self.c.post('/processos/novo',data={'aluno_id':'1','categoria':'B'},follow_redirects=True);self.assertEqual(r.status_code,200);self.assertEqual(self.scalar('SELECT COUNT(*) FROM etapas_processo'),8);self.assertEqual(self.scalar("SELECT COUNT(*) FROM etapas_processo WHERE status='CONCLUIDO'"),1)
  self.assertIn("já possui".encode(),self.c.post('/processos/novo',data={'aluno_id':'1','categoria':'B'}).data)
 def test_atualiza_etapas_e_conclui_automaticamente(self):
  self.c.post('/processos/novo',data={'aluno_id':'1','categoria':'B'})
  for etapa in range(2,9):self.c.post(f'/processos/1/etapas/{etapa}',data={'status':'CONCLUIDO'})
  self.assertEqual(self.scalar("SELECT status FROM processos_habilitacao WHERE id=1"),'CONCLUIDO');self.assertIsNotNone(self.scalar("SELECT data_conclusao FROM processos_habilitacao WHERE id=1"))
 def test_status_invalido_e_permissao(self):
  self.c.post('/processos/novo',data={'aluno_id':'1','categoria':'B'});self.assertEqual(self.c.post('/processos/1/etapas/1',data={'status':'INVALIDO'}).status_code,400)
  with self.c.session_transaction() as s:s['perfil']='INSTRUTOR'
  self.assertEqual(self.c.get('/processos').status_code,403)
if __name__=='__main__':unittest.main()
