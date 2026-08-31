from datetime import date, datetime

from flask import Blueprint, abort, render_template, request

from modules.decorators import perfis_permitidos
from services.relatorio_service import gerar_relatorios

relatorios = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios.get("")
@perfis_permitidos("ADMINISTRADOR")
def pagina():
    hoje = date.today()
    data_inicio = request.args.get("data_inicio", hoje.replace(day=1).isoformat())
    data_fim = request.args.get("data_fim", hoje.isoformat())
    try:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    except ValueError:
        abort(400, description="Período inválido.")
    if inicio > fim:
        abort(400, description="A data inicial deve ser anterior à data final.")
    instrutor_id = request.args.get("instrutor_id", type=int)
    dados = gerar_relatorios(inicio.isoformat(), fim.isoformat(), instrutor_id)
    return render_template("relatorios/pagina.html", dados=dados, data_inicio=inicio,
                           data_fim=fim, instrutor_id=instrutor_id)
