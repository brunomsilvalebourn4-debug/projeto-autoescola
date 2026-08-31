import os

from flask import Flask, render_template, redirect, session
from flask_bcrypt import Bcrypt

from config import Config
from modules.auth import auth

app = Flask(__name__)
app.config.from_object(Config)

# ============================================
# BCRYPT
# ============================================

bcrypt = Bcrypt(app)

# ============================================
# BLUEPRINTS
# ============================================

app.register_blueprint(auth)

# ============================================
# HOME
# ============================================

@app.route('/')
def home():

    if 'usuario' not in session:
        return redirect('/login')

    return redirect('/dashboard')

# ============================================
# DASHBOARD
# ============================================

@app.route('/dashboard')
def dashboard():

    if 'usuario' not in session:
        return redirect('/login')

    return render_template('dashboard.html', app_name=app.config['APP_NAME'])

# ============================================
# LOGOUT
# ============================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ============================================
# START
# ============================================

if __name__ == '__main__':

    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
