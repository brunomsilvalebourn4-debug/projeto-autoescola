import sqlite3,tempfile,unittest
from datetime import date
from pathlib import Path
from app import create_app
from services.disponibilidade_service import sugerir_instrutores
class DisponibilidadeTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.db=str(Path(self.t.name)/'t.db');self.app=create_app({'TESTING':True,'DB_NAME':self.db,'SECRET_KEY':'x'});self.c=self.app.test_client();c=sqlite3.connect(self.db);c.executescript("""INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim)VALUES('Bruno','1','1','08:00','10:30'),('Ana','2','2','08:00','10:30');INSERT INTO instrutor_categorias VALUES(1,'B'),(2,'B');INSERT INTO instrutor_disponibilidade VALUES(1,0),(2,0);INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh)VALUES('Aluno','3','3','B');INSERT INTO veiculos(placa,marca,modelo,categoria,tipo)VALUES('ABC1D23','F','M','B','A');INSERT INTO aulas(aluno_id,instrutor_id,veiculo_id,data,horario_inicio,horario_fim,categoria)VALUES(1,1,1,'2026-08-31','08:00','08:50','B');""");c.commit();c.close()
 def tearDown(self):self.t.cleanup()
 def test_ordena_por_livres_carga_e_nome(self):
  with self.app.app_context():r=sugerir_instrutores('B',date(2026,8,31),1)
  self.assertEqual(r[0]['nome'],'Ana');self.assertEqual(r[0]['horarios_livres'],3);self.assertEqual(r[1]['aulas_futuras'],1)
 def test_api_protegida(self):
  self.assertEqual(self.c.get('/api/instrutores/sugestoes?categoria=B').status_code,302)
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil='ATENDENTE')
  self.assertEqual(self.c.get('/api/instrutores/sugestoes?categoria=B').status_code,200);self.assertEqual(self.c.get('/api/instrutores/sugestoes?categoria=X').status_code,400)
if __name__=='__main__':unittest.main()
