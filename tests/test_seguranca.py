import re,sqlite3,tempfile,unittest
from pathlib import Path
from app import create_app
from werkzeug.security import generate_password_hash
class SegurancaTest(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.app=create_app({'TESTING':True,'DB_NAME':str(Path(self.t.name)/'t.db'),'SECRET_KEY':'segredo','CSRF_ENABLED':True});self.c=self.app.test_client()
 def tearDown(self):self.t.cleanup()
 def token(self,path='/login'):
  html=self.c.get(path).get_data(as_text=True);return re.search(r'name="csrf_token" value="([^"]+)',html).group(1)
 def test_csrf_bloqueia_post_sem_token(self):self.assertEqual(self.c.post('/login',data={'email':'x','senha':'x'}).status_code,400)
 def test_login_incorreto_com_csrf(self):self.assertEqual(self.c.post('/login',data={'email':'x@x.com','senha':'errada','csrf_token':self.token()}).status_code,200)
 def test_login_correto_e_senha_com_hash(self):
  con=sqlite3.connect(self.app.config['DB_NAME']);hash_senha=generate_password_hash('senha-segura');con.execute("INSERT INTO users(nome,email,senha_hash,perfil)VALUES('Admin','admin@teste.com',?,'ADMINISTRADOR')",(hash_senha,));con.commit();armazenada=con.execute('SELECT senha_hash FROM users').fetchone()[0];con.close();self.assertNotEqual(armazenada,'senha-segura')
  r=self.c.post('/login',data={'email':'admin@teste.com','senha':'senha-segura','csrf_token':self.token()},follow_redirects=False);self.assertEqual(r.status_code,302);self.assertIn('/dashboard',r.location)
 def test_gestao_usuarios_apenas_admin(self):
  self.app.config['CSRF_ENABLED']=False
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil='ATENDENTE')
  self.assertEqual(self.c.get('/usuarios').status_code,403)
  with self.c.session_transaction() as s:s['perfil']='ADMINISTRADOR'
  r=self.c.post('/usuarios/novo',data={'nome':'Novo Admin','email':'novo@teste.com','senha':'12345678','perfil':'ADMINISTRADOR','ativo':'1'},follow_redirects=True);self.assertEqual(r.status_code,200);self.assertIn(b'novo@teste.com',r.data)
if __name__=='__main__':unittest.main()
