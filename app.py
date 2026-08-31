import os

import sqlite3

from flask import Flask, jsonify, redirect, render_template, session, url_for

from config import Config
from modules.alunos import alunos
from modules.aulas import aulas
from modules.ajuda import ajuda
from modules.calendario import calendario
from modules.csrf import init_app as init_csrf
from modules.sugestoes import sugestoes
from modules.users import users
from modules.auth import auth
from modules.decorators import login_required
from modules.db import get_connection, init_app as init_database
from services.dashboard_service import obter_dashboard
from modules.instrutores import instrutores
from modules.processos import processos
from modules.relatorios import relatorios
from modules.veiculos import veiculos


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if test_config:
        application.config.update(test_config)
        if application.config.get("TESTING") and "CSRF_ENABLED" not in test_config:
            application.config["CSRF_ENABLED"] = False

    if application.config["APP_ENV"] == "production" and application.config["SECRET_KEY"] == "dev-change-me":
        raise RuntimeError("Defina uma SECRET_KEY segura antes de iniciar em produção.")

    init_database(application)
    init_csrf(application)
    application.register_blueprint(auth)
    application.register_blueprint(alunos)
    application.register_blueprint(instrutores)
    application.register_blueprint(veiculos)
    application.register_blueprint(processos)
    application.register_blueprint(aulas)
    application.register_blueprint(ajuda)
    application.register_blueprint(calendario)
    application.register_blueprint(sugestoes)
    application.register_blueprint(users)
    application.register_blueprint(relatorios)

    @application.route("/")
    def home():
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return redirect(url_for("dashboard"))

    @application.get("/health")
    def health():
        try:
            database_status = get_connection().execute("PRAGMA quick_check").fetchone()[0]
        except sqlite3.Error:
            return jsonify(status="error", database="unavailable"), 503
        if database_status != "ok":
            return jsonify(status="error", database="unhealthy"), 503
        return jsonify(status="ok", database="ok")

    @application.route("/dashboard")
    @login_required
    def dashboard():
        indicadores, etapas, situacoes = obter_dashboard()
        return render_template("dashboard.html", app_name=application.config["APP_NAME"], indicadores=indicadores, etapas=etapas, situacoes=situacoes)

    @application.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("auth.login"))

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
