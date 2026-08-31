import tempfile,unittest
from pathlib import Path
from app import create_app
class AcessibilidadeTest(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.app=create_app({'TESTING':True,'DB_NAME':str(Path(self.t.name)/'t.db'),'SECRET_KEY':'x'});self.c=self.app.test_client()
  with self.c.session_transaction() as s:s.update(user_id=1,usuario='T',perfil='ADMINISTRADOR')
 def tearDown(self):self.t.cleanup()
 def test_layout_tem_skip_menu_e_foco(self):
  h=self.c.get('/dashboard').get_data(as_text=True);self.assertIn('Pular para o conteúdo',h);self.assertIn('aria-controls="menu-principal"',h);self.assertIn('id="conteudo-principal"',h)
 def test_ajuda_nao_inventa_video_e_preve_legendas(self):
  h=self.c.get('/ajuda').get_data(as_text=True);self.assertEqual(h.count('Vídeo ainda não disponibilizado'),4);self.assertIn('legendas em português',h)
if __name__=='__main__':unittest.main()
