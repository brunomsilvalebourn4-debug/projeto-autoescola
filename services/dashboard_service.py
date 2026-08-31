from datetime import date,timedelta
from modules.db import get_connection
def obter_dashboard():
 c=get_connection();hoje=date.today();inicio=hoje-timedelta(days=hoje.weekday());fim=inicio+timedelta(days=6)
 scalar=lambda sql,p=():c.execute(sql,p).fetchone()[0]
 indicadores={'alunos_ativos':scalar("SELECT COUNT(*) FROM alunos WHERE status='ATIVO'"),'processos_andamento':scalar("SELECT COUNT(*) FROM processos_habilitacao WHERE status='EM_ANDAMENTO'"),'processos_concluidos':scalar("SELECT COUNT(*) FROM processos_habilitacao WHERE status='CONCLUIDO'"),'aulas_dia':scalar("SELECT COUNT(*) FROM aulas WHERE data=? AND situacao='AGENDADA'",(hoje.isoformat(),)),'aulas_semana':scalar("SELECT COUNT(*) FROM aulas WHERE data BETWEEN ? AND ? AND situacao NOT IN ('CANCELADA','REAGENDADA')",(inicio.isoformat(),fim.isoformat())),'instrutores_ativos':scalar("SELECT COUNT(*) FROM instrutores WHERE ativo=1"),'veiculos_disponiveis':scalar("SELECT COUNT(*) FROM veiculos WHERE status='DISPONIVEL'")}
 etapas=c.execute("SELECT e.nome,COUNT(*) total FROM etapas_processo e JOIN processos_habilitacao p ON p.id=e.processo_id WHERE e.status='EM_ANDAMENTO' AND p.status='EM_ANDAMENTO' GROUP BY e.codigo,e.nome,e.ordem ORDER BY e.ordem").fetchall()
 situacoes=c.execute("SELECT situacao,COUNT(*) total FROM aulas GROUP BY situacao ORDER BY situacao").fetchall()
 return indicadores,etapas,situacoes
