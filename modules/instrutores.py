from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modules.decorators import perfis_permitidos
from repositories.instrutor_repository import InstrutorRepository
from services.instrutor_service import CATEGORIAS, DIAS, salvar_instrutor

instrutores = Blueprint("instrutores", __name__, url_prefix="/instrutores")
CONSULTA = ("ADMINISTRADOR", "ATENDENTE")


@instrutores.route("")
@perfis_permitidos(*CONSULTA)
def listar():
    filtros = {"q": request.args.get("q", "").strip(), "ativo": request.args.get("ativo", ""), "categoria": request.args.get("categoria", "")}
    return render_template("instrutores/lista.html", instrutores=InstrutorRepository.listar(filtros["q"], filtros["ativo"], filtros["categoria"]), filtros=filtros, categorias=CATEGORIAS)


@instrutores.route("/novo", methods=["GET", "POST"])
@perfis_permitidos("ADMINISTRADOR")
def criar():
    dados, categorias, dias, erros = {}, [], [], {}
    if request.method == "POST":
        registro_id, dados, categorias, dias, erros = salvar_instrutor(request.form)
        if registro_id:
            flash("Instrutor cadastrado com sucesso.", "success")
            return redirect(url_for("instrutores.detalhe", instrutor_id=registro_id))
    return render_template("instrutores/formulario.html", instrutor=dados, selecionadas=categorias, dias_selecionados=dias, erros=erros, categorias=CATEGORIAS, dias=DIAS, titulo="Cadastrar instrutor")


@instrutores.route("/<int:instrutor_id>")
@perfis_permitidos(*CONSULTA)
def detalhe(instrutor_id):
    instrutor = InstrutorRepository.buscar(instrutor_id)
    if not instrutor: abort(404)
    return render_template("instrutores/detalhe.html", instrutor=instrutor, dias=dict(DIAS))


@instrutores.route("/<int:instrutor_id>/editar", methods=["GET", "POST"])
@perfis_permitidos("ADMINISTRADOR")
def editar(instrutor_id):
    atual = InstrutorRepository.buscar(instrutor_id)
    if not atual: abort(404)
    dados, selecionadas, dias_selecionados, erros = atual, atual.categorias, atual.dias_disponiveis, {}
    if request.method == "POST":
        salvo, dados, selecionadas, dias_selecionados, erros = salvar_instrutor(request.form, instrutor_id)
        if salvo:
            flash("Instrutor atualizado com sucesso.", "success")
            return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor_id))
    return render_template("instrutores/formulario.html", instrutor=dados, selecionadas=selecionadas, dias_selecionados=dias_selecionados, erros=erros, categorias=CATEGORIAS, dias=DIAS, titulo="Editar instrutor")


@instrutores.post("/<int:instrutor_id>/alternar-status")
@perfis_permitidos("ADMINISTRADOR")
def alternar_status(instrutor_id):
    if not InstrutorRepository.buscar(instrutor_id): abort(404)
    InstrutorRepository.alternar_ativo(instrutor_id)
    flash("Status do instrutor atualizado.", "success")
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor_id))
