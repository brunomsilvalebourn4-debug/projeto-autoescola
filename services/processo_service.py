from models.processo_habilitacao import ETAPAS_PADRAO
from repositories.processo_repository import ProcessoRepository

STATUS_ETAPA=("NAO_INICIADO","EM_ANDAMENTO","PENDENTE","CONCLUIDO")
STATUS_PROCESSO=("EM_ANDAMENTO","CONCLUIDO","CANCELADO")
RESULTADOS=("","APROVADO","REPROVADO")


def criar_processo(form):
    erros={}
    try: aluno_id=int(form.get("aluno_id",0))
    except ValueError: aluno_id=0
    categoria=(form.get("categoria") or "").upper().strip(); observacoes=(form.get("observacoes") or "").strip()
    alunos={a["id"]:a for a in ProcessoRepository.alunos_disponiveis()}
    if aluno_id not in alunos: erros["aluno_id"]="Selecione um aluno ativo."
    if categoria not in ("A","B","AB","C","D","E"): erros["categoria"]="Selecione uma categoria válida."
    if aluno_id and ProcessoRepository.existe_aberto(aluno_id): erros["aluno_id"]="Este aluno já possui um processo em andamento."
    if erros:return None,erros
    return ProcessoRepository.criar(aluno_id,categoria,observacoes,ETAPAS_PADRAO),{}
