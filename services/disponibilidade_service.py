from datetime import date,datetime,timedelta
from modules.db import get_connection

def _minutos(valor):
 h,m=map(int,valor.split(':'));return h*60+m

def sugerir_instrutores(categoria,referencia=None,dias=30):
 referencia=referencia or date.today();fim=referencia+timedelta(days=dias-1);c=get_connection()
 duracao=int(c.execute("SELECT valor FROM configuracoes WHERE chave='duracao_aula_minutos'").fetchone()[0])
 instrutores=c.execute("""SELECT i.* FROM instrutores i JOIN instrutor_categorias ic ON ic.instrutor_id=i.id WHERE i.ativo=1 AND ic.categoria=? ORDER BY i.nome""",(categoria,)).fetchall();resultado=[]
 for i in instrutores:
  dias_ativos={r[0] for r in c.execute("SELECT dia_semana FROM instrutor_disponibilidade WHERE instrutor_id=?",(i['id'],))};livres=0
  aulas=c.execute("SELECT data,horario_inicio,horario_fim FROM aulas WHERE instrutor_id=? AND data BETWEEN ? AND ? AND situacao NOT IN ('CANCELADA','REAGENDADA')",(i['id'],referencia.isoformat(),fim.isoformat())).fetchall();ocupados={}
  for a in aulas:ocupados.setdefault(a['data'],[]).append((_minutos(a['horario_inicio']),_minutos(a['horario_fim'])))
  for n in range(dias):
   atual=referencia+timedelta(days=n)
   if atual.weekday() not in dias_ativos:continue
   slot=_minutos(i['horario_inicio']);limite=_minutos(i['horario_fim'])
   while slot+duracao<=limite:
    if not any(slot<fim_a and slot+duracao>ini_a for ini_a,fim_a in ocupados.get(atual.isoformat(),[])):livres+=1
    slot+=duracao
  resultado.append({'id':i['id'],'nome':i['nome'],'horarios_livres':livres,'aulas_futuras':len(aulas)})
 return sorted(resultado,key=lambda x:(-x['horarios_livres'],x['aulas_futuras'],x['nome'].casefold()))
