"""API do app do aluno. Somente consulta: nenhuma rota altera aulas, alunos, instrutores ou veículos.

O aluno é identificado exclusivamente pelo token Bearer. Nenhuma rota aceita id de aluno.
"""

import logging
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request

from modules.csrf import isentar
from services import aluno_app_service as servico

aluno_api = isentar(Blueprint("aluno_api", __name__, url_prefix="/api/aluno"))

LIMITE_LOGIN_IP = (10, 300)
LIMITE_LOGIN_CPF = (10, 300)
LIMITE_CONSULTA = (120, 60)


@aluno_api.record_once
def configurar_log(estado):
    """Registra acessos (login, falhas, limites, logout) na saída de erros capturada pelo servidor."""
    if estado.app.testing or servico.log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    servico.log.addHandler(handler)
    servico.log.setLevel(logging.INFO)


def ip_cliente():
    saltos = current_app.config.get("ALUNO_APP_PROXIES", 0)
    encaminhados = [parte.strip() for parte in request.headers.get("X-Forwarded-For", "").split(",") if parte.strip()]
    if saltos and len(encaminhados) >= saltos:
        return encaminhados[-saltos]
    return request.remote_addr or "-"


def conexao_segura():
    if request.is_secure:
        return True
    return bool(current_app.config.get("ALUNO_APP_PROXIES")) and request.headers.get("X-Forwarded-Proto", "") == "https"


def erro(mensagem, status):
    return jsonify(erro=mensagem), status


@aluno_api.before_request
def exigir_https():
    if current_app.config.get("ALUNO_APP_EXIGIR_HTTPS") and not conexao_segura():
        return erro("Conexão segura (HTTPS) obrigatória.", 403)
    return None


@aluno_api.after_request
def cabecalhos(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    if current_app.config.get("ALUNO_APP_EXIGIR_HTTPS"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


def aluno_autenticado(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        token = cabecalho[7:].strip() if cabecalho[:7].lower() == "bearer " else ""
        sessao = servico.autenticar_token(token)
        if not sessao:
            return erro("Sessão expirada. Entre novamente.", 401)
        if not servico.limitador.permitir(f"consulta:{sessao['sessao_id']}", *LIMITE_CONSULTA):
            return erro("Muitas requisições. Aguarde um instante.", 429)
        g.aluno_id = sessao["aluno_id"]
        g.sessao_id = sessao["sessao_id"]
        return view(*args, **kwargs)
    return wrapped


def _dados():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


def _limitar_acesso(cpf):
    ip = ip_cliente()
    permitido_ip = servico.limitador.permitir(f"login-ip:{ip}", *LIMITE_LOGIN_IP)
    permitido_cpf = servico.limitador.permitir(f"login-cpf:{servico.somente_digitos(cpf)}", *LIMITE_LOGIN_CPF)
    if not (permitido_ip and permitido_cpf):
        servico.log.warning("app_aluno_limite_excedido ip=%s", ip)
        return erro("Muitas tentativas. Aguarde alguns minutos e tente novamente.", 429)
    return None


@aluno_api.post("/login")
def login():
    dados = _dados()
    cpf, nascimento = str(dados.get("cpf", "")), str(dados.get("data_nascimento", ""))
    bloqueio = _limitar_acesso(cpf)
    if bloqueio:
        return bloqueio
    try:
        return jsonify(servico.entrar(cpf, nascimento, ip_cliente()))
    except servico.ErroAcesso as falha:
        return erro(falha.mensagem, falha.status)


@aluno_api.post("/logout")
@aluno_autenticado
def logout():
    servico.sair(g.sessao_id, g.aluno_id, ip_cliente())
    return "", 204


@aluno_api.get("/perfil")
@aluno_autenticado
def perfil():
    return jsonify(servico.perfil(g.aluno_id))


@aluno_api.get("/resumo")
@aluno_autenticado
def resumo():
    return jsonify(servico.resumo(g.aluno_id))


@aluno_api.get("/aulas")
@aluno_autenticado
def aulas():
    return jsonify(servico.aulas_do_aluno(g.aluno_id))


@aluno_api.get("/aulas/<int:aula_id>")
@aluno_autenticado
def aula(aula_id):
    registro = servico.aula(g.aluno_id, aula_id)
    if not registro:
        return erro("Aula não encontrada.", 404)
    return jsonify(registro)
