"""Gestão administrativa do acesso ao app do aluno (gerar código de ativação e revogar)."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for

from modules.decorators import perfis_permitidos
from repositories.aluno_repository import AlunoRepository
from services import aluno_app_service as servico

aluno_acesso = Blueprint("aluno_acesso", __name__, url_prefix="/alunos")
ACESSO = ("ADMINISTRADOR", "ATENDENTE")


@aluno_acesso.app_template_global("acesso_app_aluno")
def acesso_app_aluno(aluno_id):
    return servico.status_acesso(aluno_id)


def _aluno(aluno_id):
    aluno = AlunoRepository.buscar(aluno_id)
    if not aluno:
        abort(404)
    return aluno


@aluno_acesso.post("/<int:aluno_id>/app-aluno/codigo")
@perfis_permitidos(*ACESSO)
def gerar_codigo(aluno_id):
    aluno = _aluno(aluno_id)
    if aluno.status in servico.STATUS_ALUNO_BLOQUEADO:
        flash("Alunos inativos ou cancelados não podem acessar o app.", "error")
        return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))
    codigo, expira = servico.gerar_codigo(aluno_id)
    # O código é exibido somente nesta resposta; apenas o hash fica gravado.
    return render_template("alunos/detalhe.html", aluno=aluno, codigo_app=codigo, codigo_app_expira=expira)


@aluno_acesso.post("/<int:aluno_id>/app-aluno/revogar")
@perfis_permitidos(*ACESSO)
def revogar(aluno_id):
    _aluno(aluno_id)
    servico.revogar(aluno_id)
    flash("Acesso ao app do aluno revogado.", "success")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))
