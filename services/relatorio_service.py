from modules.db import get_connection


def gerar_relatorios(data_inicio, data_fim, instrutor_id=None):
    connection = get_connection()
    alunos_ativos = connection.execute(
        "SELECT id,nome_completo,cpf,telefone,categoria_cnh FROM alunos WHERE status='ATIVO' ORDER BY nome_completo"
    ).fetchall()
    alunos_etapa = connection.execute("""
        SELECT e.nome etapa, COUNT(*) total
        FROM etapas_processo e
        JOIN processos_habilitacao p ON p.id=e.processo_id
        WHERE p.status='EM_ANDAMENTO' AND e.status='EM_ANDAMENTO'
        GROUP BY e.codigo,e.nome,e.ordem ORDER BY e.ordem
    """).fetchall()

    filtros = ["au.data BETWEEN ? AND ?"]
    parametros = [data_inicio, data_fim]
    if instrutor_id:
        filtros.append("au.instrutor_id=?")
        parametros.append(instrutor_id)
    aulas = connection.execute(f"""
        SELECT au.data,au.horario_inicio,au.horario_fim,au.situacao,
               a.nome_completo aluno,i.nome instrutor,v.placa
        FROM aulas au JOIN alunos a ON a.id=au.aluno_id
        JOIN instrutores i ON i.id=au.instrutor_id
        JOIN veiculos v ON v.id=au.veiculo_id
        WHERE {' AND '.join(filtros)} ORDER BY au.data,au.horario_inicio
    """, parametros).fetchall()
    aulas_instrutor = connection.execute("""
        SELECT i.nome instrutor, COUNT(au.id) total,
        SUM(CASE WHEN au.situacao='REALIZADA' THEN 1 ELSE 0 END) realizadas,
        SUM(CASE WHEN au.situacao='CANCELADA' THEN 1 ELSE 0 END) canceladas
        FROM instrutores i LEFT JOIN aulas au ON au.instrutor_id=i.id AND au.data BETWEEN ? AND ?
        WHERE (? IS NULL OR i.id = ?)
        GROUP BY i.id,i.nome HAVING COUNT(au.id)>0 ORDER BY total DESC,i.nome
    """, (data_inicio, data_fim, instrutor_id, instrutor_id)).fetchall()
    processos = connection.execute("""
        SELECT p.data_conclusao,p.resultado,p.categoria,a.nome_completo
        FROM processos_habilitacao p JOIN alunos a ON a.id=p.aluno_id
        WHERE p.status='CONCLUIDO' AND p.data_conclusao BETWEEN ? AND ?
        ORDER BY p.data_conclusao DESC
    """, (data_inicio, data_fim)).fetchall()
    resultados = connection.execute("""
        SELECT COALESCE(resultado,'SEM_RESULTADO') resultado,COUNT(*) total
        FROM processos_habilitacao
        WHERE status='CONCLUIDO' AND data_conclusao BETWEEN ? AND ?
        GROUP BY resultado ORDER BY resultado
    """, (data_inicio, data_fim)).fetchall()
    instrutores = connection.execute("SELECT id,nome FROM instrutores ORDER BY nome").fetchall()
    return {
        "alunos_ativos": alunos_ativos,
        "alunos_etapa": alunos_etapa,
        "aulas": aulas,
        "aulas_instrutor": aulas_instrutor,
        "processos": processos,
        "resultados": resultados,
        "instrutores": instrutores,
    }
