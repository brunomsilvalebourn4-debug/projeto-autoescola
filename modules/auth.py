from flask import Blueprint, current_app, render_template, request, redirect, session, url_for
from modules.db import get_connection
from werkzeug.security import check_password_hash

auth = Blueprint('auth', __name__)

# =========================================
# LOGIN
# =========================================
@auth.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        senha = request.form.get('senha')

        if not email or not senha:
            return render_template('login.html', erro='Preencha todos os campos')

        conn = get_connection()

        usuario = conn.execute(
            "SELECT * FROM users WHERE email = ? AND ativo = 1",
            (email,)
        ).fetchone()

        conn.close()

        if usuario and check_password_hash(usuario['senha_hash'], senha):

            # 🔥 LIMPA SESSÃO ANTERIOR
            session.clear()

            # 🔥 GARANTE SESSÃO PERSISTENTE
            session.permanent = True
            session.modified = True

            # 🔥 DEFINE USUÁRIO LOGADO
            session['user_id'] = usuario['id']
            session['usuario'] = usuario['nome']
            session['perfil'] = usuario['perfil']
            session['instrutor_id'] = usuario['instrutor_id']

            return redirect(url_for('dashboard'))

        return render_template('login.html', erro='Email ou senha inválidos')

    return render_template('login.html', app_name=current_app.config['APP_NAME'])
