import json
import logging
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from app import create_app
from services import aluno_app_service

AGORA = datetime(2026, 9, 28, 10, 0)

DADOS = """
INSERT INTO alunos(nome_completo,cpf,telefone,email,categoria_cnh,data_nascimento) VALUES
 ('João Pereira','52998224725','11999999999','joao@teste.com','B','2004-05-17'),
 ('Maria Souza','11144477735','11999999998',NULL,'B','2006-11-02'),
 ('Pedro Sem Data','93541134780','11999999997',NULL,'B',NULL);
INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim) VALUES
 ('Carlos Henrique','12345678909','1190','07:00','19:00'),
 ('Marcos Silva','93541134780','1191','07:00','19:00');
INSERT INTO veiculos(placa,marca,modelo,categoria,tipo) VALUES
 ('ABC1D23','Fiat','Mobi','B','AUTOMOVEL'),
 ('DEF2E34','Hyundai','HB20','B','AUTOMOVEL');
INSERT INTO aulas(id,aluno_id,instrutor_id,veiculo_id,data,horario_inicio,horario_fim,categoria,situacao,observacoes) VALUES
 (1,1,1,1,'2026-09-20','09:00','09:50','B','REALIZADA','nota interna'),
 (2,1,2,2,'2026-09-21','09:00','09:50','B','REALIZADA',NULL),
 (3,1,1,1,'2026-09-22','09:00','09:50','B','FALTA',NULL),
 (4,1,1,1,'2026-09-25','09:00','09:50','B','AGENDADA',NULL),
 (5,1,1,1,'2026-09-28','11:00','11:50','B','AGENDADA',NULL),
 (6,1,2,2,'2026-09-29','14:00','15:00','B','AGENDADA',NULL),
 (7,1,1,1,'2026-09-28','10:30','11:00','B','CANCELADA',NULL),
 (8,1,1,1,'2026-09-30','08:00','08:50','B','REAGENDADA',NULL),
 (9,2,2,2,'2026-09-28','10:15','11:00','B','AGENDADA',NULL);
"""


class AlunoAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("autoescola.app_aluno").setLevel(logging.CRITICAL)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "t.db")
        self.app = create_app({"TESTING": True, "DB_NAME": self.db, "SECRET_KEY": "x"})
        self.c = self.app.test_client()
        con = sqlite3.connect(self.db)
        con.executescript(DADOS)
        con.commit()
        con.close()
        self.agora = AGORA
        relogio = patch.object(aluno_app_service, "agora", side_effect=lambda: self.agora)
        relogio.start()
        self.addCleanup(relogio.stop)
        aluno_app_service.limitador.limpar()

    def tearDown(self):
        self.tmp.cleanup()

    # ---- auxiliares -----------------------------------------------

    def sql(self, consulta, parametros=()):
        con = sqlite3.connect(self.db)
        try:
            return con.execute(consulta, parametros).fetchall()
        finally:
            con.close()

    def como_equipe(self, perfil="ATENDENTE"):
        with self.c.session_transaction() as s:
            s.clear()
            s.update(user_id=1, usuario="Equipe", perfil=perfil)

    def login(self, cpf="529.982.247-25", nascimento="2004-05-17", **kw):
        return self.c.post("/api/aluno/login", json={"cpf": cpf, "data_nascimento": nascimento}, **kw)

    def token(self, cpf="529.982.247-25", nascimento="2004-05-17"):
        r = self.login(cpf, nascimento)
        self.assertEqual(r.status_code, 200, r.get_json())
        return r.get_json()["token"]

    def sql_exec(self, comando):
        con = sqlite3.connect(self.db)
        con.execute(comando)
        con.commit()
        con.close()

    def get(self, caminho, token):
        return self.c.get(caminho, headers={"Authorization": f"Bearer {token}"})

    # ---- autenticação --------------------------------------------

    def test_login_com_cpf_e_data_de_nascimento(self):
        r = self.login("52998224725", "2004-05-17")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["nome"], "João Pereira")
        token = r.get_json()["token"]
        self.assertEqual(self.sql("SELECT COUNT(*) FROM aluno_sessoes WHERE token_hash=?", (token,))[0][0], 0, "token não é gravado em claro")
        self.assertEqual(self.get("/api/aluno/perfil", token).status_code, 200)
        self.assertEqual(self.login("529.982.247-25", "17/05/2004").status_code, 200, "aceita DD/MM/AAAA")

    def test_dados_que_nao_conferem(self):
        for cpf, nascimento in [("52998224725", "2004-05-18"), ("52998224725", ""), ("52998224725", "31/02/2004"),
                                ("11144477735", "2004-05-17"), ("00000000000", "2004-05-17")]:
            aluno_app_service.limitador.limpar()
            r = self.login(cpf, nascimento)
            self.assertEqual(r.status_code, 401, (cpf, nascimento))
            self.assertEqual(r.get_json()["erro"], "CPF ou data de nascimento não conferem com o cadastro da autoescola.")

    def test_aluno_sem_data_de_nascimento_nao_entra(self):
        self.assertEqual(self.login("93541134780", "").status_code, 401)
        self.assertEqual(self.login("93541134780", "2000-01-01").status_code, 401)

    def test_token_ausente_invalido_expirado_e_logout(self):
        self.assertEqual(self.c.get("/api/aluno/resumo").status_code, 401)
        self.assertEqual(self.get("/api/aluno/resumo", "invalido").status_code, 401)
        token = self.token()
        self.assertEqual(self.get("/api/aluno/resumo", token).status_code, 200)
        self.agora = AGORA + timedelta(days=31)
        self.assertEqual(self.get("/api/aluno/resumo", token).status_code, 401)
        self.agora = AGORA
        token = self.token()
        self.assertEqual(self.c.post("/api/aluno/logout", headers={"Authorization": f"Bearer {token}"}).status_code, 204)
        self.assertEqual(self.get("/api/aluno/resumo", token).status_code, 401)

    def test_bloqueio_pela_equipe_e_status_do_aluno(self):
        token = self.token()
        self.como_equipe()
        self.c.post("/alunos/1/app-aluno/bloquear")
        self.assertEqual(self.get("/api/aluno/resumo", token).status_code, 401, "bloqueio encerra sessões abertas")
        self.assertEqual(self.login().status_code, 401)

        self.como_equipe()
        self.c.post("/alunos/1/app-aluno/desbloquear")
        token = self.token()
        self.sql_exec("UPDATE alunos SET status='INATIVO' WHERE id=1")
        self.assertEqual(self.get("/api/aluno/resumo", token).status_code, 401)
        self.assertEqual(self.login().status_code, 401)

    def test_limite_de_tentativas_por_origem_e_bloqueio_da_conta(self):
        for dia in range(1, 6):
            self.assertEqual(self.login(nascimento=f"2004-05-0{dia}").status_code, 401)
        self.assertEqual(self.login().status_code, 429, "conta bloqueada após 5 falhas, mesmo com a data certa")
        self.agora = AGORA + timedelta(minutes=16)
        self.assertEqual(self.login().status_code, 200)

        aluno_app_service.limitador.limpar()
        respostas = [self.login(f"000000000{n:02d}", "2000-01-01").status_code for n in range(11)]
        self.assertEqual(respostas[:10], [401] * 10)
        self.assertEqual(respostas[10], 429, "limite por IP")

    # ---- isolamento ----------------------------------------------

    def test_aluno_so_ve_as_proprias_aulas(self):
        token_joao = self.token("52998224725", "2004-05-17")
        token_maria = self.token("11144477735", "2006-11-02")

        aulas = self.get("/api/aluno/aulas?aluno_id=2", token_joao).get_json()
        ids = {a["id"] for grupo in ("proximas", "realizadas", "outras") for a in aulas[grupo]}
        self.assertEqual(ids, {1, 2, 3, 4, 5, 6, 7, 8})

        self.assertEqual(self.get("/api/aluno/aulas/9", token_joao).status_code, 404)
        self.assertEqual(self.get("/api/aluno/aulas/1", token_maria).status_code, 404)
        self.assertEqual(self.get("/api/aluno/aulas/9", token_maria).status_code, 200)
        self.assertEqual(self.get("/api/aluno/2/aulas", token_joao).status_code, 404)

        resumo_maria = self.get("/api/aluno/resumo", token_maria).get_json()
        self.assertEqual(resumo_maria["proxima_aula"]["id"], 9)
        self.assertEqual(resumo_maria["contagem"]["na_grade"], 1)
        self.assertEqual(self.get("/api/aluno/perfil", token_maria).get_json()["nome"], "Maria Souza")

    def test_resposta_nao_expoe_dados_internos(self):
        token = self.token()
        aula = self.get("/api/aluno/aulas/1", token).get_json()
        self.assertNotIn("observacoes", aula)
        self.assertNotIn("aluno_id", aula)
        self.assertEqual(set(aula["instrutor"]), {"nome"})
        perfil = self.get("/api/aluno/perfil", token).get_json()
        self.assertEqual(perfil["cpf"], "***.982.247-**")

    # ---- consulta ------------------------------------------------

    def test_proxima_aula(self):
        token = self.token()
        proxima = self.get("/api/aluno/resumo", token).get_json()["proxima_aula"]
        self.assertEqual(proxima["id"], 5, "ignora cancelada, passada e aula de outro aluno")
        self.assertEqual(proxima["dia_semana"], "Segunda-feira")
        self.assertEqual((proxima["horario_inicio"], proxima["horario_fim"], proxima["duracao_minutos"]), ("11:00", "11:50", 50))

        self.agora = datetime(2026, 9, 28, 11, 20)
        proxima = self.get("/api/aluno/resumo", token).get_json()["proxima_aula"]
        self.assertEqual((proxima["id"], proxima["status"]), (5, "em_andamento"))

        self.agora = datetime(2026, 9, 28, 12, 0)
        self.assertEqual(self.get("/api/aluno/resumo", token).get_json()["proxima_aula"]["id"], 6)

        self.agora = datetime(2026, 10, 1, 8, 0)
        self.assertIsNone(self.get("/api/aluno/resumo", token).get_json()["proxima_aula"])

    def test_contagem_segue_situacoes_do_sistema(self):
        token = self.token()
        contagem = self.get("/api/aluno/resumo", token).get_json()["contagem"]
        self.assertEqual(contagem, {
            "contratadas": None, "na_grade": 5, "realizadas": 2, "agendadas": 2, "aguardando_registro": 1,
            "restantes": 3, "faltas": 1, "canceladas": 1, "reagendadas": 1, "percentual": 40,
        })

        self.sql_exec("UPDATE aulas SET situacao='REALIZADA' WHERE id=4")
        contagem = self.get("/api/aluno/resumo", token).get_json()["contagem"]
        self.assertEqual((contagem["realizadas"], contagem["restantes"], contagem["percentual"]), (3, 2, 60),
                         "alteração administrativa aparece na próxima consulta")

    def test_listas_e_ordenacao(self):
        token = self.token()
        aulas = self.get("/api/aluno/aulas", token).get_json()
        self.assertEqual([a["id"] for a in aulas["proximas"]], [5, 6])
        self.assertEqual([a["id"] for a in aulas["realizadas"]], [2, 1])
        self.assertEqual({a["id"]: a["status"] for a in aulas["outras"]},
                         {8: "reagendada", 7: "cancelada", 4: "aguardando_registro", 3: "falta"})

    def test_instrutor_e_veiculo(self):
        token = self.token()
        aula = self.get("/api/aluno/aulas/6", token).get_json()
        self.assertEqual(aula["instrutor"]["nome"], "Marcos Silva")
        self.assertEqual(aula["veiculo"], {"marca": "Hyundai", "modelo": "HB20", "placa": "DEF2E34"})
        self.assertEqual((aula["data"], aula["dia_semana"], aula["categoria"]), ("2026-09-29", "Terça-feira", "B"))

        self.sql_exec("UPDATE aulas SET instrutor_id=1, veiculo_id=1 WHERE id=6")
        aula = self.get("/api/aluno/aulas/6", token).get_json()
        self.assertEqual((aula["instrutor"]["nome"], aula["veiculo"]["placa"]), ("Carlos Henrique", "ABC1D23"))

    # ---- somente leitura -----------------------------------------

    def test_api_nao_altera_a_grade(self):
        token = self.token()
        antes = self.sql("SELECT * FROM aulas ORDER BY id")
        cab = {"Authorization": f"Bearer {token}"}
        for metodo in ("put", "patch", "delete", "post"):
            self.assertEqual(getattr(self.c, metodo)("/api/aluno/aulas/5", headers=cab, json={"situacao": "CANCELADA"}).status_code, 405)
        self.assertEqual(self.c.post("/api/aluno/aulas", headers=cab, json={}).status_code, 405)
        for caminho in ("/api/aluno/resumo", "/api/aluno/aulas", "/api/aluno/aulas/5", "/api/aluno/perfil"):
            r = self.get(caminho, token)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.headers["Cache-Control"], "no-store")
        self.assertEqual(self.sql("SELECT * FROM aulas ORDER BY id"), antes)

    def test_token_do_aluno_nao_da_acesso_ao_sistema_administrativo(self):
        token = self.token()
        cab = {"Authorization": f"Bearer {token}"}
        for caminho in ("/aulas", "/alunos", "/calendario", "/dashboard"):
            self.assertEqual(self.c.get(caminho, headers=cab).status_code, 302)

    # ---- área administrativa -------------------------------------

    def test_apenas_equipe_bloqueia_acesso(self):
        self.assertEqual(self.c.post("/alunos/1/app-aluno/bloquear").status_code, 302)
        self.assertEqual(self.login().status_code, 200, "sem sessão da equipe, nada é bloqueado")
        self.como_equipe("INSTRUTOR")
        self.assertEqual(self.c.post("/alunos/1/app-aluno/bloquear").status_code, 403)
        self.assertEqual(self.c.post("/alunos/1/app-aluno/desbloquear").status_code, 403)
        self.como_equipe("ADMINISTRADOR")
        self.assertEqual(self.c.post("/alunos/99/app-aluno/bloquear").status_code, 404)

    def test_detalhe_do_aluno_exibe_situacao_do_acesso(self):
        self.como_equipe()
        self.assertIn("Liberado", self.c.get("/alunos/1").get_data(as_text=True))
        self.assertIn("cadastre a data de nascimento", self.c.get("/alunos/3").get_data(as_text=True))
        self.c.post("/alunos/1/app-aluno/bloquear")
        html = self.c.get("/alunos/1").get_data(as_text=True)
        self.assertIn("Bloqueado pela equipe", html)
        self.assertIn("Desbloquear acesso", html)

    # ---- transporte e PWA ----------------------------------------

    def test_csrf_continua_nas_rotas_da_equipe_e_nao_se_aplica_a_api_por_token(self):
        app = create_app({"TESTING": True, "DB_NAME": self.db, "SECRET_KEY": "x", "CSRF_ENABLED": True})
        cliente = app.test_client()
        self.assertEqual(cliente.post("/api/aluno/login", json={"cpf": "52998224725", "data_nascimento": "2004-05-17"}).status_code, 200)
        with cliente.session_transaction() as s:
            s.update(user_id=1, usuario="Equipe", perfil="ATENDENTE")
        self.assertEqual(cliente.post("/alunos/1/app-aluno/bloquear").status_code, 400)

    def test_https_obrigatorio_em_producao(self):
        self.app.config.update(ALUNO_APP_EXIGIR_HTTPS=True, ALUNO_APP_PROXIES=1)
        self.assertEqual(self.c.get("/api/aluno/resumo").status_code, 403)
        r = self.c.get("/app/")
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.location.startswith("https://"))
        r = self.c.get("/api/aluno/resumo", headers={"X-Forwarded-Proto": "https"})
        self.assertEqual(r.status_code, 401)
        self.assertIn("Strict-Transport-Security", r.headers)

    def test_ip_do_cliente_atras_do_proxy(self):
        self.app.config.update(ALUNO_APP_PROXIES=1)
        for n in range(10):
            self.login(f"000000000{n:02d}", "2000-01-01", headers={"X-Forwarded-For": "1.1.1.1"})
        bloqueado = self.login("00000000099", "2000-01-01", headers={"X-Forwarded-For": "1.1.1.1"})
        outro = self.login("00000000099", "2000-01-01", headers={"X-Forwarded-For": "2.2.2.2"})
        self.assertEqual((bloqueado.status_code, outro.status_code), (429, 401))

    def test_app_instalavel(self):
        self.assertEqual(self.c.get("/app").status_code, 302)
        r = self.c.get("/app/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("script-src 'self'", r.headers["Content-Security-Policy"])
        self.assertIn(b"app_aluno/app.js", r.data)
        manifest = self.c.get("/app/manifest.webmanifest")
        self.assertEqual(manifest.mimetype, "application/manifest+json")
        self.assertEqual(json.loads(manifest.data)["start_url"], "/app/")
        sw = self.c.get("/app/sw.js")
        self.assertEqual(sw.mimetype, "text/javascript")
        self.assertIn(b"/api/", sw.data)
        for arquivo in ("app.js", "app.css", "icon.svg", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
            with self.c.get(f"/static/app_aluno/{arquivo}") as r:
                self.assertEqual(r.status_code, 200, arquivo)


if __name__ == "__main__":
    unittest.main()
