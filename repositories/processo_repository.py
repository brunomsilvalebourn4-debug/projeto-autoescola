from datetime import date

from modules.db import get_connection


class ProcessoRepository:
    @staticmethod
    def listar(termo="", status=""):
        filtros, params = [], []
        if termo:
            filtros.append("(a.nome_completo LIKE ? OR a.cpf LIKE ?)"); params.extend((f"%{termo}%", f"%{termo}%"))
        if status:
            filtros.append("p.status=?"); params.append(status)
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        return get_connection().execute(f"""SELECT p.*, a.nome_completo, a.cpf,
            COUNT(e.id) total_etapas, SUM(CASE WHEN e.status='CONCLUIDO' THEN 1 ELSE 0 END) etapas_concluidas
            FROM processos_habilitacao p JOIN alunos a ON a.id=p.aluno_id LEFT JOIN etapas_processo e ON e.processo_id=p.id
            {where} GROUP BY p.id ORDER BY p.id DESC""", params).fetchall()

    @staticmethod
    def buscar(processo_id):
        connection = get_connection()
        processo = connection.execute("SELECT p.*,a.nome_completo,a.cpf FROM processos_habilitacao p JOIN alunos a ON a.id=p.aluno_id WHERE p.id=?", (processo_id,)).fetchone()
        etapas = connection.execute("SELECT * FROM etapas_processo WHERE processo_id=? ORDER BY ordem", (processo_id,)).fetchall()
        return processo, etapas

    @staticmethod
    def alunos_disponiveis():
        return get_connection().execute("SELECT id,nome_completo,cpf,categoria_cnh FROM alunos WHERE status='ATIVO' ORDER BY nome_completo").fetchall()

    @staticmethod
    def existe_aberto(aluno_id):
        return get_connection().execute("SELECT 1 FROM processos_habilitacao WHERE aluno_id=? AND status='EM_ANDAMENTO'", (aluno_id,)).fetchone() is not None

    @staticmethod
    def criar(aluno_id, categoria, observacoes, etapas_padrao):
        connection = get_connection(); hoje = date.today().isoformat()
        try:
            cursor = connection.execute("INSERT INTO processos_habilitacao (aluno_id,categoria,data_inicio,observacoes) VALUES (?,?,?,?)", (aluno_id,categoria,hoje,observacoes))
            processo_id = cursor.lastrowid
            connection.executemany("""INSERT INTO etapas_processo
                (processo_id,codigo,nome,ordem,status,data_inicio,data_conclusao)
                VALUES (?,?,?,?,?,?,?)""", ((processo_id,codigo,nome,ordem,"CONCLUIDO" if ordem==1 else "NAO_INICIADO",hoje if ordem==1 else None,hoje if ordem==1 else None) for codigo,nome,ordem in etapas_padrao))
            connection.commit(); return processo_id
        except Exception:
            connection.rollback(); raise

    @staticmethod
    def atualizar_etapa(processo_id, etapa_id, status, observacoes):
        connection = get_connection(); hoje=date.today().isoformat()
        etapa = connection.execute("SELECT * FROM etapas_processo WHERE id=? AND processo_id=?", (etapa_id,processo_id)).fetchone()
        if not etapa: return False
        inicio = etapa["data_inicio"]; conclusao = None
        if status in ("EM_ANDAMENTO","CONCLUIDO") and not inicio: inicio=hoje
        if status=="CONCLUIDO": conclusao=hoje
        connection.execute("UPDATE etapas_processo SET status=?,data_inicio=?,data_conclusao=?,observacoes=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?", (status,inicio,conclusao,observacoes,etapa_id))
        pendentes = connection.execute("SELECT COUNT(*) FROM etapas_processo WHERE processo_id=? AND status!='CONCLUIDO'", (processo_id,)).fetchone()[0]
        connection.execute("UPDATE processos_habilitacao SET status=?,data_conclusao=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=? AND status!='CANCELADO'", ("CONCLUIDO" if pendentes==0 else "EM_ANDAMENTO", hoje if pendentes==0 else None, processo_id))
        connection.commit(); return True

    @staticmethod
    def atualizar_processo(processo_id,status,resultado,observacoes):
        connection=get_connection(); conclusao=date.today().isoformat() if status=="CONCLUIDO" else None
        connection.execute("UPDATE processos_habilitacao SET status=?,resultado=?,observacoes=?,data_conclusao=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?",(status,resultado or None,observacoes,conclusao,processo_id)); connection.commit()
