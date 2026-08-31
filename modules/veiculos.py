from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from modules.decorators import perfis_permitidos
from repositories.veiculo_repository import VeiculoRepository
from services.veiculo_service import CATEGORIAS, STATUS, salvar_veiculo

veiculos = Blueprint("veiculos", __name__, url_prefix="/veiculos")
CONSULTA = ("ADMINISTRADOR", "ATENDENTE")


@veiculos.route("")
@perfis_permitidos(*CONSULTA)
def listar():
    filtros = {"q": request.args.get("q", "").strip(), "status": request.args.get("status", ""), "categoria": request.args.get("categoria", "")}
    return render_template("veiculos/lista.html", veiculos=VeiculoRepository.listar(filtros["q"], filtros["status"], filtros["categoria"]), filtros=filtros, categorias=CATEGORIAS, statuses=STATUS)


@veiculos.route("/novo", methods=["GET", "POST"])
@perfis_permitidos("ADMINISTRADOR")
def criar():
    dados, erros = {}, {}
    if request.method == "POST":
        registro_id, dados, erros = salvar_veiculo(request.form)
        if registro_id:
            flash("Veículo cadastrado com sucesso.", "success")
            return redirect(url_for("veiculos.detalhe", veiculo_id=registro_id))
    return render_template("veiculos/formulario.html", veiculo=dados, erros=erros, categorias=CATEGORIAS, statuses=STATUS, titulo="Cadastrar veículo")


@veiculos.route("/<int:veiculo_id>")
@perfis_permitidos(*CONSULTA)
def detalhe(veiculo_id):
    veiculo = VeiculoRepository.buscar(veiculo_id)
    if not veiculo: abort(404)
    return render_template("veiculos/detalhe.html", veiculo=veiculo)


@veiculos.route("/<int:veiculo_id>/editar", methods=["GET", "POST"])
@perfis_permitidos("ADMINISTRADOR")
def editar(veiculo_id):
    atual = VeiculoRepository.buscar(veiculo_id)
    if not atual: abort(404)
    dados, erros = atual, {}
    if request.method == "POST":
        salvo, dados, erros = salvar_veiculo(request.form, veiculo_id)
        if salvo:
            flash("Veículo atualizado com sucesso.", "success")
            return redirect(url_for("veiculos.detalhe", veiculo_id=veiculo_id))
    return render_template("veiculos/formulario.html", veiculo=dados, erros=erros, categorias=CATEGORIAS, statuses=STATUS, titulo="Editar veículo")
