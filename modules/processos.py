from flask import Blueprint,abort,flash,redirect,render_template,request,url_for
from modules.decorators import perfis_permitidos
from repositories.processo_repository import ProcessoRepository
from services.processo_service import RESULTADOS,STATUS_ETAPA,STATUS_PROCESSO,criar_processo

processos=Blueprint("processos",__name__,url_prefix="/processos"); ACESSO=("ADMINISTRADOR","ATENDENTE")

@processos.get("")
@perfis_permitidos(*ACESSO)
def listar():
    q=request.args.get("q","").strip(); status=request.args.get("status","")
    return render_template("processos/lista.html",processos=ProcessoRepository.listar(q,status),q=q,status_filtro=status,statuses=STATUS_PROCESSO)

@processos.route("/novo",methods=["GET","POST"])
@perfis_permitidos(*ACESSO)
def criar():
    erros={}
    if request.method=="POST":
        processo_id,erros=criar_processo(request.form)
        if processo_id: flash("Processo criado com as etapas padrão.","success"); return redirect(url_for("processos.detalhe",processo_id=processo_id))
    dados = request.form if request.method == "POST" else request.args
    return render_template("processos/formulario.html",alunos=ProcessoRepository.alunos_disponiveis(),erros=erros,dados=dados,categorias=("A","B","AB","C","D","E"))

@processos.get("/<int:processo_id>")
@perfis_permitidos(*ACESSO)
def detalhe(processo_id):
    processo,etapas=ProcessoRepository.buscar(processo_id)
    if not processo:abort(404)
    concluidas=sum(e["status"]=="CONCLUIDO" for e in etapas); progresso=round(concluidas/len(etapas)*100) if etapas else 0
    return render_template("processos/detalhe.html",processo=processo,etapas=etapas,progresso=progresso,status_etapa=STATUS_ETAPA,statuses=STATUS_PROCESSO,resultados=RESULTADOS)

@processos.post("/<int:processo_id>/etapas/<int:etapa_id>")
@perfis_permitidos(*ACESSO)
def atualizar_etapa(processo_id,etapa_id):
    status=request.form.get("status","")
    if status not in STATUS_ETAPA:abort(400)
    if not ProcessoRepository.atualizar_etapa(processo_id,etapa_id,status,(request.form.get("observacoes") or "").strip()):abort(404)
    flash("Etapa atualizada.","success"); return redirect(url_for("processos.detalhe",processo_id=processo_id))

@processos.post("/<int:processo_id>/status")
@perfis_permitidos(*ACESSO)
def atualizar_status(processo_id):
    processo,_=ProcessoRepository.buscar(processo_id)
    if not processo:abort(404)
    status=request.form.get("status",""); resultado=request.form.get("resultado","")
    if status not in STATUS_PROCESSO or resultado not in RESULTADOS:abort(400)
    ProcessoRepository.atualizar_processo(processo_id,status,resultado,(request.form.get("observacoes") or "").strip()); flash("Processo atualizado.","success")
    return redirect(url_for("processos.detalhe",processo_id=processo_id))
