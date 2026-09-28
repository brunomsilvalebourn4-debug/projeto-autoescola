from datetime import date,datetime,timedelta
from flask import Blueprint,abort,render_template,request,session
from modules.decorators import perfis_permitidos
from repositories.calendario_repository import CalendarioRepository
from services.aula_service import SITUACOES

calendario=Blueprint('calendario',__name__,url_prefix='/calendario')

@calendario.get('')
@perfis_permitidos('ADMINISTRADOR','ATENDENTE','INSTRUTOR')
def semanal():
 valor=request.args.get('semana','')
 try:referencia=datetime.strptime(valor,'%Y-%m-%d').date() if valor else date.today()
 except ValueError:abort(400)
 inicio=referencia-timedelta(days=referencia.weekday());fim=inicio+timedelta(days=6)
 instrutor_id=request.args.get('instrutor_id',type=int);perfil=session.get('perfil')
 if perfil=='INSTRUTOR':
  instrutor_id=session.get('instrutor_id')
  if not instrutor_id:abort(403)
 situacao=request.args.get('situacao','');aluno=request.args.get('aluno','').strip()
 if situacao and situacao not in SITUACOES:abort(400)
 registros=CalendarioRepository.aulas(inicio.isoformat(),fim.isoformat(),instrutor_id,situacao,aluno)
 por_dia={ (inicio+timedelta(days=n)).isoformat():[] for n in range(7)}
 for aula in registros:por_dia[aula['data']].append(aula)
 resumo=[]
 for categoria in sorted({a['categoria'] for a in registros}):
  grupo=[a for a in registros if a['categoria']==categoria]
  resumo.append({'categoria':categoria,'total':len(grupo),**{s:sum(a['situacao']==s for a in grupo) for s in SITUACOES}})
 return render_template('calendario/semanal.html',registros=registros,resumo=resumo,por_dia=por_dia,inicio=inicio,fim=fim,anterior=inicio-timedelta(days=7),proxima=inicio+timedelta(days=7),instrutores=CalendarioRepository.instrutores(),instrutor_id=instrutor_id,situacao=situacao,aluno=aluno,situacoes=SITUACOES,perfil=perfil)
