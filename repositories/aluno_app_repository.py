from modules.db import get_connection


class AlunoAppRepository:
    """Consultas do app do aluno. Toda leitura de aulas é filtrada pelo aluno autenticado."""

    CAMPOS_AULA = """au.id, au.data, au.horario_inicio, au.horario_fim, au.categoria, au.situacao,
        i.nome AS instrutor_nome, v.marca AS veiculo_marca, v.modelo AS veiculo_modelo, v.placa AS veiculo_placa"""

    # ---- credenciais -------------------------------------------------

    @staticmethod
    def buscar_por_cpf(cpf):
        return get_connection().execute(
            """SELECT a.id AS aluno_id, a.nome_completo, a.status AS aluno_status,
                      ac.senha_hash, ac.codigo_hash, ac.codigo_expira_em, ac.ativo,
                      ac.tentativas_falhas, ac.bloqueado_ate
               FROM alunos a LEFT JOIN aluno_acessos ac ON ac.aluno_id = a.id
               WHERE a.cpf = ?""",
            (cpf,),
        ).fetchone()

    @staticmethod
    def acesso(aluno_id):
        return get_connection().execute("SELECT * FROM aluno_acessos WHERE aluno_id = ?", (aluno_id,)).fetchone()

    @staticmethod
    def registrar_falha(aluno_id, limite, bloqueado_ate):
        connection = get_connection()
        connection.execute(
            """UPDATE aluno_acessos
               SET tentativas_falhas = tentativas_falhas + 1,
                   bloqueado_ate = CASE WHEN tentativas_falhas + 1 >= ? THEN ? ELSE bloqueado_ate END,
                   atualizado_em = CURRENT_TIMESTAMP
               WHERE aluno_id = ?""",
            (limite, bloqueado_ate, aluno_id),
        )
        connection.execute(
            "UPDATE aluno_acessos SET tentativas_falhas = 0 WHERE aluno_id = ? AND tentativas_falhas >= ?",
            (aluno_id, limite),
        )
        connection.commit()

    @staticmethod
    def registrar_sucesso(aluno_id, agora):
        connection = get_connection()
        connection.execute(
            """UPDATE aluno_acessos SET tentativas_falhas = 0, bloqueado_ate = NULL, ultimo_acesso = ?,
               atualizado_em = CURRENT_TIMESTAMP WHERE aluno_id = ?""",
            (agora, aluno_id),
        )
        connection.commit()

    @staticmethod
    def definir_codigo(aluno_id, codigo_hash, expira_em):
        connection = get_connection()
        connection.execute(
            """INSERT INTO aluno_acessos (aluno_id, codigo_hash, codigo_expira_em, ativo)
               VALUES (?, ?, ?, 1)
               ON CONFLICT(aluno_id) DO UPDATE SET codigo_hash = excluded.codigo_hash,
                   codigo_expira_em = excluded.codigo_expira_em, ativo = 1, tentativas_falhas = 0,
                   bloqueado_ate = NULL, atualizado_em = CURRENT_TIMESTAMP""",
            (aluno_id, codigo_hash, expira_em),
        )
        connection.commit()

    @staticmethod
    def definir_senha(aluno_id, senha_hash):
        """Grava a nova senha, consome o código e encerra sessões anteriores."""
        connection = get_connection()
        connection.execute(
            """UPDATE aluno_acessos SET senha_hash = ?, codigo_hash = NULL, codigo_expira_em = NULL,
               tentativas_falhas = 0, bloqueado_ate = NULL, atualizado_em = CURRENT_TIMESTAMP
               WHERE aluno_id = ?""",
            (senha_hash, aluno_id),
        )
        connection.execute("DELETE FROM aluno_sessoes WHERE aluno_id = ?", (aluno_id,))
        connection.commit()

    @staticmethod
    def revogar(aluno_id):
        connection = get_connection()
        connection.execute(
            """UPDATE aluno_acessos SET ativo = 0, codigo_hash = NULL, codigo_expira_em = NULL,
               atualizado_em = CURRENT_TIMESTAMP WHERE aluno_id = ?""",
            (aluno_id,),
        )
        connection.execute("DELETE FROM aluno_sessoes WHERE aluno_id = ?", (aluno_id,))
        connection.commit()

    # ---- sessões -----------------------------------------------------

    @staticmethod
    def criar_sessao(aluno_id, token_hash, expira_em, agora):
        connection = get_connection()
        connection.execute("DELETE FROM aluno_sessoes WHERE expira_em <= ?", (agora,))
        connection.execute(
            "INSERT INTO aluno_sessoes (aluno_id, token_hash, expira_em, ultimo_uso) VALUES (?, ?, ?, ?)",
            (aluno_id, token_hash, expira_em, agora),
        )
        connection.commit()

    @staticmethod
    def sessao_valida(token_hash, agora):
        return get_connection().execute(
            """SELECT s.id AS sessao_id, s.aluno_id
               FROM aluno_sessoes s
               JOIN aluno_acessos ac ON ac.aluno_id = s.aluno_id AND ac.ativo = 1
               JOIN alunos a ON a.id = s.aluno_id AND a.status NOT IN ('INATIVO', 'CANCELADO')
               WHERE s.token_hash = ? AND s.expira_em > ?""",
            (token_hash, agora),
        ).fetchone()

    @staticmethod
    def tocar_sessao(sessao_id, agora):
        connection = get_connection()
        connection.execute("UPDATE aluno_sessoes SET ultimo_uso = ? WHERE id = ?", (agora, sessao_id))
        connection.commit()

    @staticmethod
    def encerrar_sessao(sessao_id):
        connection = get_connection()
        connection.execute("DELETE FROM aluno_sessoes WHERE id = ?", (sessao_id,))
        connection.commit()

    # ---- consulta (somente leitura) ----------------------------------

    @staticmethod
    def perfil(aluno_id):
        return get_connection().execute(
            "SELECT id, nome_completo, cpf, email, categoria_cnh, status FROM alunos WHERE id = ?",
            (aluno_id,),
        ).fetchone()

    @classmethod
    def aulas(cls, aluno_id):
        return get_connection().execute(
            f"""SELECT {cls.CAMPOS_AULA}
                FROM aulas au
                JOIN instrutores i ON i.id = au.instrutor_id
                JOIN veiculos v ON v.id = au.veiculo_id
                WHERE au.aluno_id = ?
                ORDER BY au.data, au.horario_inicio""",
            (aluno_id,),
        ).fetchall()

    @classmethod
    def aula(cls, aluno_id, aula_id):
        return get_connection().execute(
            f"""SELECT {cls.CAMPOS_AULA}
                FROM aulas au
                JOIN instrutores i ON i.id = au.instrutor_id
                JOIN veiculos v ON v.id = au.veiculo_id
                WHERE au.id = ? AND au.aluno_id = ?""",
            (aula_id, aluno_id),
        ).fetchone()
