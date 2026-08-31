from datetime import datetime
from modules.db import get_connection

SITUACOES=("AGENDADA","REALIZADA","CANCELADA","REAGENDADA","FALTA")

def opcoes():
 c=get_connection()
 return (c.execute("SELECT id,nome_completo,categoria_cnh FROM alunos WHERE status='ATIVO' ORDER BY nome_completo").fetchall(),c.execute("SELECT id,nome,horario_inicio,horario_fim FROM instrutores WHERE ativo=1 ORDER BY nome").fetchall(),c.execute("SELECT id,placa,marca,modelo,categoria FROM veiculos WHERE status='DISPONIVEL' ORDER BY placa").fetchall())

def salvar(form,aula_id=None):
 c=get_connection(); erros=[]
 try:
  aluno_id=int(form.get('aluno_id',0));instrutor_id=int(form.get('instrutor_id',0));veiculo_id=int(form.get('veiculo_id',0))
 except ValueError: aluno_id=instrutor_id=veiculo_id=0
 data=form.get('data','');inicio=form.get('horario_inicio','');fim=form.get('horario_fim','');categoria=form.get('categoria','').upper();situacao=form.get('situacao','AGENDADA');obs=form.get('observacoes','').strip()
 try: dia=datetime.strptime(data,'%Y-%m-%d').weekday()
 except ValueError: erros.append('Informe uma data válida.');dia=-1
 if not inicio or not fim or inicio>=fim:erros.append('O horário final deve ser posterior ao inicial.')
 aluno=c.execute("SELECT * FROM alunos WHERE id=? AND status='ATIVO'",(aluno_id,)).fetchone();instrutor=c.execute("SELECT * FROM instrutores WHERE id=? AND ativo=1",(instrutor_id,)).fetchone();veiculo=c.execute("SELECT * FROM veiculos WHERE id=? AND status='DISPONIVEL'",(veiculo_id,)).fetchone()
 if not aluno:erros.append('Selecione um aluno ativo.')
 if not instrutor:erros.append('Selecione um instrutor ativo.')
 if not veiculo:erros.append('Selecione um veículo disponível.')
 if instrutor and (inicio<instrutor['horario_inicio'] or fim>instrutor['horario_fim']):erros.append('Horário fora do expediente do instrutor.')
 if instrutor and not c.execute("SELECT 1 FROM instrutor_disponibilidade WHERE instrutor_id=? AND dia_semana=?",(instrutor_id,dia)).fetchone():erros.append('Instrutor indisponível neste dia.')
 if instrutor and not c.execute("SELECT 1 FROM instrutor_categorias WHERE instrutor_id=? AND categoria=?",(instrutor_id,categoria)).fetchone():erros.append('Instrutor não habilitado para esta categoria.')
 if veiculo and veiculo['categoria']!=categoria:erros.append('Veículo incompatível com a categoria.')
 if situacao not in SITUACOES:erros.append('Situação inválida.')
 if not erros and situacao not in ('CANCELADA','REAGENDADA'):
  conflito=c.execute("""SELECT CASE WHEN aluno_id=? THEN 'aluno' WHEN instrutor_id=? THEN 'instrutor' ELSE 'veículo' END recurso FROM aulas WHERE data=? AND situacao NOT IN ('CANCELADA','REAGENDADA') AND id!=? AND horario_inicio<? AND horario_fim>? AND (aluno_id=? OR instrutor_id=? OR veiculo_id=?) LIMIT 1""",(aluno_id,instrutor_id,data,aula_id or 0,fim,inicio,aluno_id,instrutor_id,veiculo_id)).fetchone()
  if conflito:erros.append(f"Conflito de horário para {conflito['recurso']}.")
 if erros:return None,erros
 valores=(aluno_id,instrutor_id,veiculo_id,data,inicio,fim,categoria,situacao,obs)
 if aula_id:c.execute("UPDATE aulas SET aluno_id=?,instrutor_id=?,veiculo_id=?,data=?,horario_inicio=?,horario_fim=?,categoria=?,situacao=?,observacoes=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?",(*valores,aula_id))
 else:aula_id=c.execute("INSERT INTO aulas(aluno_id,instrutor_id,veiculo_id,data,horario_inicio,horario_fim,categoria,situacao,observacoes) VALUES(?,?,?,?,?,?,?,?,?)",valores).lastrowid
 c.commit();return aula_id,[]
