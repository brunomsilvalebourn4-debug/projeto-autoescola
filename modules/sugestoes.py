from flask import Blueprint,jsonify,request
from modules.decorators import perfis_permitidos
from services.disponibilidade_service import sugerir_instrutores
sugestoes=Blueprint('sugestoes',__name__,url_prefix='/api/instrutores')
@sugestoes.get('/sugestoes')
@perfis_permitidos('ADMINISTRADOR','ATENDENTE')
def listar():
 categoria=request.args.get('categoria','').upper()
 if categoria not in ('A','B','C','D','E'):return jsonify({'erro':'Categoria inválida.'}),400
 opcoes=sugerir_instrutores(categoria);return jsonify({'sugestao':opcoes[0] if opcoes else None,'opcoes':opcoes})
