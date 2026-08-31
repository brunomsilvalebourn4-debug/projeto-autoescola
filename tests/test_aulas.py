import sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app
class AulasTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.db=str(Path(self.t.name)/'t.db');self.app=create_app({'TESTING':True,'DB_NAME':self.db,'SECRET_KEY':'x'});self.c=self.app.test_client()
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil='ATENDENTE')
  c=sqlite3.connect(self.db);c.executescript("""INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh) VALUES('A','52998224725','11999999999','B'),('B','11144477735','11999999998','B');INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim) VALUES('I','12345678909','11999999999','08:00','18:00'),('J','93541134780','11999999998','08:00','18:00');INSERT INTO instrutor_categorias VALUES(1,'B'),(2,'B');INSERT INTO instrutor_disponibilidade VALUES(1,0),(2,0);INSERT INTO veiculos(placa,marca,modelo,categoria,tipo) VALUES('ABC1D23','Fiat','Mobi','B','Auto'),('DEF2E34','VW','Polo','B','Auto');""");c.commit();c.close()
 def tearDown(self):self.t.cleanup()
 def dados(self,**kw):
  d={'aluno_id':'1','instrutor_id':'1','veiculo_id':'1','data':'2026-08-31','horario_inicio':'09:00','horario_fim':'09:50','categoria':'B','situacao':'AGENDADA'};d.update(kw);return d
 def test_agenda_e_conflitos_parciais(self):
  self.assertEqual(self.c.post('/aulas/nova',data=self.dados(),follow_redirects=True).status_code,200)
  for campo,valor,texto in [('aluno_id','1','aluno'),('instrutor_id','1','instrutor'),('veiculo_id','1','veículo')]:
   d=self.dados(aluno_id='2',instrutor_id='2',veiculo_id='2',horario_inicio='09:30',horario_fim='10:20');d[campo]=valor
   self.assertIn(texto.encode(),self.c.post('/aulas/nova',data=d).data)
 def test_expediente_dia_categoria_e_status(self):
  self.assertIn('expediente'.encode(),self.c.post('/aulas/nova',data=self.dados(horario_inicio='07:00',horario_fim='07:50')).data)
  self.assertIn('indisponível'.encode(),self.c.post('/aulas/nova',data=self.dados(data='2026-09-01')).data)
  self.assertIn('habilitado'.encode(),self.c.post('/aulas/nova',data=self.dados(categoria='A')).data)
 def test_cancelamento_libera_horario(self):
  self.c.post('/aulas/nova',data=self.dados());self.c.post('/aulas/1/situacao',data={'situacao':'CANCELADA'});self.assertNotIn('Conflito'.encode(),self.c.post('/aulas/nova',data=self.dados()).data)
if __name__=='__main__':unittest.main()
