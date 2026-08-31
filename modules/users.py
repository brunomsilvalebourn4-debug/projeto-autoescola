from flask import Blueprint,abort,flash,redirect,render_template,request,url_for
from modules.decorators import perfis_permitidos
from repositories.user_repository import UserRepository
from services.user_service import PERFIS,salvar_usuario
users=Blueprint('users',__name__,url_prefix='/usuarios')
@users.get('')
@perfis_permitidos('ADMINISTRADOR')
def listar():return render_template('usuarios/lista.html',usuarios=UserRepository.listar())
@users.route('/novo',methods=['GET','POST'])
@perfis_permitidos('ADMINISTRADOR')
def criar():
 dados={};erros={}
 if request.method=='POST':
  uid,dados,erros=salvar_usuario(request.form)
  if uid:flash('Usuário criado com sucesso.','success');return redirect(url_for('users.listar'))
 return render_template('usuarios/formulario.html',usuario=dados,erros=erros,perfis=PERFIS,instrutores=UserRepository.instrutores(),titulo='Novo usuário')
@users.route('/<int:user_id>/editar',methods=['GET','POST'])
@perfis_permitidos('ADMINISTRADOR')
def editar(user_id):
 atual=UserRepository.buscar(user_id)
 if not atual:abort(404)
 dados=atual;erros={}
 if request.method=='POST':
  uid,dados,erros=salvar_usuario(request.form,user_id)
  if uid:flash('Usuário atualizado.','success');return redirect(url_for('users.listar'))
 return render_template('usuarios/formulario.html',usuario=dados,erros=erros,perfis=PERFIS,instrutores=UserRepository.instrutores(),titulo='Editar usuário')
