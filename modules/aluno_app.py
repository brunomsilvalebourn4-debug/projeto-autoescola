"""Entrega do app do aluno (PWA instalável em Android e iPhone) em /app/."""

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from modules.aluno_api import conexao_segura

aluno_app = Blueprint("aluno_app", __name__, url_prefix="/app")
VERSAO = "1.0.0"

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
       "manifest-src 'self'; worker-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'")


@aluno_app.before_request
def exigir_https():
    if current_app.config.get("ALUNO_APP_EXIGIR_HTTPS") and not conexao_segura():
        return redirect(request.url.replace("http://", "https://", 1), code=301)
    return None


@aluno_app.after_request
def cabecalhos(response):
    response.headers["Content-Security-Policy"] = CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if current_app.config.get("ALUNO_APP_EXIGIR_HTTPS"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


@aluno_app.get("")
def raiz():
    return redirect(url_for("aluno_app.shell"))


@aluno_app.get("/")
def shell():
    response = current_app.make_response(render_template("app_aluno/index.html", versao=VERSAO))
    response.headers["Cache-Control"] = "no-cache"
    return response


@aluno_app.get("/manifest.webmanifest")
def manifest():
    response = current_app.make_response(render_template("app_aluno/manifest.webmanifest", versao=VERSAO))
    response.mimetype = "application/manifest+json"
    return response


@aluno_app.get("/sw.js")
def service_worker():
    response = current_app.make_response(render_template("app_aluno/sw.js", versao=VERSAO))
    response.mimetype = "text/javascript"
    response.headers["Cache-Control"] = "no-cache"
    return response
