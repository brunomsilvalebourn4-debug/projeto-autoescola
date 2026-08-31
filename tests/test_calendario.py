import sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app
class CalendarioTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.db=str(Path(self.t.name)/'t.db');self.app=create_app({'TESTING':True,'DB_NAME':self.db,'SECRET_KEY':'x'});self.c=self.app.test_client();con=sqlite3.connect(self.db);con.executescript("""INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh)VALUES('Ana','52998224725','1199','B');INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim)VALUES('Joao','11144477735','1199','08:00','18:00'),('Jose','12345678909','1198','08:00','18:00');INSERT INTO veiculos(placa,marca,modelo,categoria,tipo)VALUES('ABC1D23','F','M','B','A');INSERT INTO aulas(aluno_id,instrutor_id,veiculo_id,data,horario_inicio,horario_fim,categoria)VALUES(1,1,1,'2026-08-31','09:00','09:50','B');""");con.commit();con.close()
 def tearDown(self):self.t.cleanup()
 def login(self,perfil='ATENDENTE',iid=None):
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil=perfil,instrutor_id=iid)
 def test_semana_global_filtros_e_navegacao(self):
  self.login();r=self.c.get('/calendario?semana=2026-09-02&aluno=Ana&situacao=AGENDADA');self.assertEqual(r.status_code,200);self.assertIn(b'Ana',r.data);self.assertIn(b'Semana anterior',r.data)
 def test_instrutor_so_ve_propria_agenda(self):
  self.login('INSTRUTOR',2);r=self.c.get('/calendario?semana=2026-08-31&instrutor_id=1');self.assertNotIn(b'Ana',r.data)
  self.login('INSTRUTOR',1);self.assertIn(b'Ana',self.c.get('/calendario?semana=2026-08-31').data)
 def test_instrutor_sem_vinculo_bloqueado(self):
  self.login('INSTRUTOR');self.assertEqual(self.c.get('/calendario').status_code,403)
if __name__=='__main__':unittest.main()
