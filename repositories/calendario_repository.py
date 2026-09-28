from modules.db import get_connection


class CalendarioRepository:
 @staticmethod
 def instrutores():
  return get_connection().execute("SELECT id,nome FROM instrutores WHERE ativo=1 ORDER BY nome").fetchall()
 @staticmethod
 def aulas(inicio,fim,instrutor_id=None,situacao="",aluno=""):
  filtros=["au.data BETWEEN ? AND ?"];params=[inicio,fim]
  if instrutor_id:filtros.append("au.instrutor_id=?");params.append(instrutor_id)
  if situacao:filtros.append("au.situacao=?");params.append(situacao)
  if aluno:filtros.append("a.nome_completo LIKE ?");params.append(f"%{aluno}%")
  return get_connection().execute(f"""SELECT au.*,a.nome_completo,i.nome instrutor,v.placa,v.marca,v.modelo
   FROM aulas au JOIN alunos a ON a.id=au.aluno_id JOIN instrutores i ON i.id=au.instrutor_id JOIN veiculos v ON v.id=au.veiculo_id
   WHERE {' AND '.join(filtros)} ORDER BY au.data,au.horario_inicio""",params).fetchall()
