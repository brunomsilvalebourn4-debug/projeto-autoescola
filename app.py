import os

from flask import Flask, redirect, render_template, session, url_for

from config import Config
from modules.alunos import alunos
from modules.aulas import aulas
from modules.calendario import calendario
from modules.sugestoes import sugestoes
from modules.auth import auth
from modules.decorators import login_required
from modules.db import init_app as init_database
from services.dashboard_service import obter_dashboard
from modules.instrutores import instrutores
from modules.processos import processos
from modules.veiculos import veiculos


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if test_config:
        application.config.update(test_config)

    init_database(application)
    application.register_blueprint(auth)
    application.register_blueprint(alunos)
    application.register_blueprint(instrutores)
    application.register_blueprint(veiculos)
    application.register_blueprint(processos)
    application.register_blueprint(aulas)
    application.register_blueprint(calendario)
    application.register_blueprint(sugestoes)

    @application.route("/")
    def home():
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return redirect(url_for("dashboard"))

    @application.route("/dashboard")
    @login_required
    def dashboard():
        indicadores, etapas, situacoes = obter_dashboard()
        return render_template("dashboard.html", app_name=application.config["APP_NAME"], indicadores=indicadores, etapas=etapas, situacoes=situacoes)

    @application.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("auth.login"))

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
