from flask import Blueprint,abort,flash,redirect,render_template,request,url_for
from modules.db import get_connection
from modules.decorators import perfis_permitidos
from services.aula_service import SITUACOES,opcoes,salvar
aulas=Blueprint('aulas',__name__,url_prefix='/aulas');ACESSO=('ADMINISTRADOR','ATENDENTE')
@aulas.get('')
@perfis_permitidos(*ACESSO)
def listar():
 rows=get_connection().execute("SELECT au.*,a.nome_completo,i.nome instrutor,v.placa FROM aulas au JOIN alunos a ON a.id=au.aluno_id JOIN instrutores i ON i.id=au.instrutor_id JOIN veiculos v ON v.id=au.veiculo_id ORDER BY au.data DESC,au.horario_inicio").fetchall();return render_template('aulas/lista.html',aulas=rows)
@aulas.route('/nova',methods=['GET','POST'])
@perfis_permitidos(*ACESSO)
def criar():
 erros=[]
 if request.method=='POST':
  aid,erros=salvar(request.form)
  if aid:flash('Aula agendada com sucesso.','success');return redirect(url_for('aulas.listar'))
 alunos,instrutores,veiculos=opcoes();return render_template('aulas/formulario.html',dados=request.form,erros=erros,alunos=alunos,instrutores=instrutores,veiculos=veiculos,situacoes=SITUACOES)
@aulas.post('/<int:aula_id>/situacao')
@perfis_permitidos(*ACESSO)
def situacao(aula_id):
 estado=request.form.get('situacao');
 if estado not in SITUACOES:abort(400)
 c=get_connection();cur=c.execute("UPDATE aulas SET situacao=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?",(estado,aula_id));c.commit()
 if not cur.rowcount:abort(404)
 flash('Situação da aula atualizada.','success');return redirect(url_for('aulas.listar'))
