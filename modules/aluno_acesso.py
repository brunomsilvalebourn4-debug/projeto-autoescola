"""Gestão administrativa do acesso ao app do aluno (bloquear e desbloquear)."""

from flask import Blueprint, abort, flash, redirect, url_for

from modules.decorators import perfis_permitidos
from repositories.aluno_repository import AlunoRepository
from services import aluno_app_service as servico

aluno_acesso = Blueprint("aluno_acesso", __name__, url_prefix="/alunos")
ACESSO = ("ADMINISTRADOR", "ATENDENTE")


@aluno_acesso.app_template_global("acesso_app_aluno")
def acesso_app_aluno(aluno_id):
    return servico.status_acesso(aluno_id)


def _aluno(aluno_id):
    if not AlunoRepository.buscar(aluno_id):
        abort(404)


@aluno_acesso.post("/<int:aluno_id>/app-aluno/bloquear")
@perfis_permitidos(*ACESSO)
def bloquear(aluno_id):
    _aluno(aluno_id)
    servico.bloquear(aluno_id)
    flash("Acesso ao app do aluno bloqueado.", "success")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))


@aluno_acesso.post("/<int:aluno_id>/app-aluno/desbloquear")
@perfis_permitidos(*ACESSO)
def desbloquear(aluno_id):
    _aluno(aluno_id)
    servico.desbloquear(aluno_id)
    flash("Acesso ao app do aluno desbloqueado.", "success")
    return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))
