from flask import Blueprint,render_template
from modules.decorators import login_required
ajuda=Blueprint('ajuda',__name__,url_prefix='/ajuda')
@ajuda.get('')
@login_required
def pagina():
 tutoriais=[{'titulo':'Como cadastrar um aluno','descricao':'Cadastro, endereço e categoria pretendida.'},{'titulo':'Como acompanhar um processo','descricao':'Etapas, andamento e conclusão.'},{'titulo':'Como agendar uma aula','descricao':'Recursos, horários e conflitos.'},{'titulo':'Como utilizar o calendário','descricao':'Visão semanal e filtros.'}]
 return render_template('ajuda.html',tutoriais=tutoriais)
