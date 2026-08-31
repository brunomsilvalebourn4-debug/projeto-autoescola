import math

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modules.decorators import perfis_permitidos
from repositories.aluno_repository import AlunoRepository
from services.aluno_service import CATEGORIAS, STATUS, salvar


alunos = Blueprint("alunos", __name__, url_prefix="/alunos")
ACESSO_ALUNOS = ("ADMINISTRADOR", "ATENDENTE")


@alunos.route("")
@perfis_permitidos(*ACESSO_ALUNOS)
def listar():
    termo = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip().upper()
    try:
        pagina = max(1, int(request.args.get("page", 1)))
    except ValueError:
        pagina = 1
    por_pagina = 10
    registros, total = AlunoRepository.listar(termo, status, pagina, por_pagina)
    total_paginas = max(1, math.ceil(total / por_pagina))
    if pagina > total_paginas:
        return redirect(url_for("alunos.listar", q=termo, status=status, page=total_paginas))
    return render_template("alunos/lista.html", alunos=registros, total=total, pagina=pagina,
                           total_paginas=total_paginas, termo=termo, status_filtro=status, statuses=STATUS)


@alunos.route("/novo", methods=["GET", "POST"])
@perfis_permitidos(*ACESSO_ALUNOS)
def criar():
    dados, erros = {}, {}
    if request.method == "POST":
        aluno_id, dados, erros = salvar(request.form)
        if aluno_id:
            flash("Aluno cadastrado com sucesso.", "success")
            return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))
    return render_template("alunos/formulario.html", aluno=dados, erros=erros, categorias=CATEGORIAS,
                           statuses=STATUS, titulo="Cadastrar aluno")


@alunos.route("/<int:aluno_id>")
@perfis_permitidos(*ACESSO_ALUNOS)
def detalhe(aluno_id):
    aluno = AlunoRepository.buscar(aluno_id)
    if not aluno:
        abort(404)
    return render_template("alunos/detalhe.html", aluno=aluno)


@alunos.route("/<int:aluno_id>/editar", methods=["GET", "POST"])
@perfis_permitidos(*ACESSO_ALUNOS)
def editar(aluno_id):
    aluno = AlunoRepository.buscar(aluno_id)
    if not aluno:
        abort(404)
    dados, erros = aluno, {}
    if request.method == "POST":
        salvo_id, dados, erros = salvar(request.form, aluno_id)
        if salvo_id:
            flash("Aluno atualizado com sucesso.", "success")
            return redirect(url_for("alunos.detalhe", aluno_id=aluno_id))
    return render_template("alunos/formulario.html", aluno=dados, erros=erros, categorias=CATEGORIAS,
                           statuses=STATUS, titulo="Editar aluno")
