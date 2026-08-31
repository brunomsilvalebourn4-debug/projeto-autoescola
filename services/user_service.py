import sqlite3
from werkzeug.security import generate_password_hash
from repositories.user_repository import UserRepository

PERFIS=("ADMINISTRADOR","ATENDENTE","INSTRUTOR")
def salvar_usuario(form,user_id=None):
 nome=(form.get('nome') or '').strip();email=(form.get('email') or '').strip().lower();perfil=form.get('perfil','');senha=form.get('senha','');ativo=1 if form.get('ativo','1')=='1' else 0;erros={};instrutor_id=None
 if len(nome)<3:erros['nome']='Informe o nome.'
 if '@' not in email:erros['email']='Informe um e-mail válido.'
 if perfil not in PERFIS:erros['perfil']='Perfil inválido.'
 if not user_id and len(senha)<8:erros['senha']='A senha deve ter pelo menos 8 caracteres.'
 if senha and len(senha)<8:erros['senha']='A senha deve ter pelo menos 8 caracteres.'
 if perfil=='INSTRUTOR':
  try:instrutor_id=int(form.get('instrutor_id',0))
  except ValueError:instrutor_id=0
  if not any(i['id']==instrutor_id for i in UserRepository.instrutores()):erros['instrutor_id']='Selecione um instrutor ativo.'
 dados={'nome':nome,'email':email,'perfil':perfil,'instrutor_id':instrutor_id,'ativo':ativo,'senha_hash':generate_password_hash(senha) if senha else ''}
 if erros:return None,dados,erros
 try:return UserRepository.salvar(dados,user_id),dados,{}
 except sqlite3.IntegrityError:
  erros['email']='Este e-mail já está em uso.';return None,dados,erros
