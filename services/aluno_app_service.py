"""Regras do app do aluno: autenticação própria e consulta somente leitura das aulas.

As situações seguem exatamente as do sistema web (models/aula.py). A contagem de progresso
considera a grade registrada: aulas REALIZADA + AGENDADA. CANCELADA e REAGENDADA ficam fora da
grade, como no restante do sistema (conflitos, disponibilidade e dashboard). O sistema não possui
quantidade de aulas contratadas; por isso nenhum valor "contratado" é inventado aqui.
"""

import hashlib
import logging
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from repositories.aluno_app_repository import AlunoAppRepository

log = logging.getLogger("autoescola.app_aluno")

FORMATO_DATA_HORA = "%Y-%m-%d %H:%M:%S"
DIAS_SEMANA = ("Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo")
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LIMITE_FALHAS_CONTA = 5
MINUTOS_BLOQUEIO = 15
STATUS_ALUNO_BLOQUEADO = ("INATIVO", "CANCELADO")
# Hash fixo usado quando o CPF não existe, para igualar o tempo de resposta.
_HASH_FICTICIO = generate_password_hash(secrets.token_urlsafe(16))


class ErroAcesso(Exception):
    def __init__(self, mensagem, status=401):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


# ---- relógio -------------------------------------------------------------

def _fuso():
    nome = current_app.config.get("APP_TIMEZONE", "America/Sao_Paulo")
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(nome)
    except Exception:
        # Windows sem o pacote tzdata. O Brasil não adota horário de verão desde 2019.
        if nome == "America/Sao_Paulo":
            return timezone(timedelta(hours=-3))
        return None


def agora():
    """Data e hora locais da Autoescola, sem fuso (mesmo formato gravado nas aulas)."""
    fuso = _fuso()
    return datetime.now(fuso).replace(tzinfo=None) if fuso else datetime.now()


def _texto(momento):
    return momento.strftime(FORMATO_DATA_HORA)


# ---- limitação de tentativas por origem ---------------------------------

class LimitadorTaxa:
    """Janela deslizante em memória. Suficiente para o worker único usado na publicação."""

    def __init__(self):
        self._eventos = defaultdict(deque)
        self._trava = threading.Lock()

    def permitir(self, chave, limite, janela_segundos):
        instante = time.monotonic()
        with self._trava:
            eventos = self._eventos[chave]
            while eventos and instante - eventos[0] > janela_segundos:
                eventos.popleft()
            if len(eventos) >= limite:
                return False
            eventos.append(instante)
            return True

    def limpar(self):
        with self._trava:
            self._eventos.clear()


limitador = LimitadorTaxa()


# ---- credenciais ---------------------------------------------------------

def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def mascarar_cpf(cpf):
    cpf = somente_digitos(cpf)
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**" if len(cpf) == 11 else "***"


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def normalizar_codigo(codigo):
    return re.sub(r"[^A-Z0-9]", "", (codigo or "").upper())


def gerar_codigo(aluno_id):
    """Gera um código de ativação de uso único. Retorna o código em claro uma única vez."""
    codigo = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
    expira = agora() + timedelta(hours=current_app.config["ALUNO_APP_CODIGO_HORAS"])
    AlunoAppRepository.definir_codigo(aluno_id, generate_password_hash(codigo), _texto(expira))
    log.info("codigo_app_gerado aluno_id=%s", aluno_id)
    return f"{codigo[:4]}-{codigo[4:]}", expira


def revogar(aluno_id):
    AlunoAppRepository.revogar(aluno_id)
    log.info("acesso_app_revogado aluno_id=%s", aluno_id)


def status_acesso(aluno_id):
    acesso = AlunoAppRepository.acesso(aluno_id)
    if not acesso:
        return {"situacao": "SEM_ACESSO"}
    if not acesso["ativo"]:
        return {"situacao": "REVOGADO"}
    if acesso["senha_hash"]:
        return {"situacao": "ATIVO", "ultimo_acesso": acesso["ultimo_acesso"], "codigo_pendente": bool(acesso["codigo_hash"])}
    return {"situacao": "AGUARDANDO_ATIVACAO", "codigo_expira_em": acesso["codigo_expira_em"]}


def _conta_para(cpf):
    """Retorna a conta utilizável ou None, sempre com o mesmo tempo aproximado."""
    conta = AlunoAppRepository.buscar_por_cpf(cpf) if len(cpf) == 11 else None
    if not conta or conta["ativo"] != 1 or conta["aluno_status"] in STATUS_ALUNO_BLOQUEADO:
        return None
    return conta


def _verificar_bloqueio(conta, momento):
    if conta["bloqueado_ate"] and conta["bloqueado_ate"] > _texto(momento):
        raise ErroAcesso("Muitas tentativas. Aguarde alguns minutos e tente novamente.", 429)


def _falhar(conta, momento, motivo, ip):
    if conta:
        AlunoAppRepository.registrar_falha(conta["aluno_id"], LIMITE_FALHAS_CONTA, _texto(momento + timedelta(minutes=MINUTOS_BLOQUEIO)))
    log.warning("app_aluno_falha motivo=%s aluno_id=%s ip=%s", motivo, conta["aluno_id"] if conta else "-", ip)


def _emitir_sessao(conta, momento, ip, evento):
    token = secrets.token_urlsafe(32)
    expira = momento + timedelta(days=current_app.config["ALUNO_APP_TOKEN_DIAS"])
    AlunoAppRepository.criar_sessao(conta["aluno_id"], hash_token(token), _texto(expira), _texto(momento))
    AlunoAppRepository.registrar_sucesso(conta["aluno_id"], _texto(momento))
    log.info("%s aluno_id=%s ip=%s", evento, conta["aluno_id"], ip)
    return {"token": token, "expira_em": expira.isoformat(timespec="seconds"), "nome": conta["nome_completo"]}


def entrar(cpf, senha, ip):
    cpf = somente_digitos(cpf)
    momento = agora()
    conta = _conta_para(cpf)
    if conta:
        _verificar_bloqueio(conta, momento)
    senha_hash = conta["senha_hash"] if conta and conta["senha_hash"] else _HASH_FICTICIO
    if not senha or not check_password_hash(senha_hash, senha) or not conta or not conta["senha_hash"]:
        _falhar(conta, momento, "login", ip)
        raise ErroAcesso("CPF ou senha inválidos.")
    return _emitir_sessao(conta, momento, ip, "app_aluno_login")


def validar_senha_nova(senha, confirmacao, cpf):
    if len(senha or "") < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if len(senha) > 128:
        return "A senha deve ter no máximo 128 caracteres."
    if senha != confirmacao:
        return "As senhas não conferem."
    if somente_digitos(senha) == cpf or len(set(senha)) < 4:
        return "Escolha uma senha menos previsível."
    return None


def ativar(cpf, codigo, senha, confirmacao, ip):
    """Primeiro acesso ou redefinição: troca o código entregue pela Autoescola por uma senha."""
    cpf = somente_digitos(cpf)
    erro_senha = validar_senha_nova(senha, confirmacao, cpf)
    if erro_senha:
        raise ErroAcesso(erro_senha, 400)
    momento = agora()
    conta = _conta_para(cpf)
    if conta:
        _verificar_bloqueio(conta, momento)
    codigo_hash = conta["codigo_hash"] if conta and conta["codigo_hash"] else _HASH_FICTICIO
    valido = check_password_hash(codigo_hash, normalizar_codigo(codigo))
    if not conta or not conta["codigo_hash"] or not valido or conta["codigo_expira_em"] <= _texto(momento):
        _falhar(conta, momento, "ativacao", ip)
        raise ErroAcesso("CPF ou código de acesso inválido ou expirado.")
    AlunoAppRepository.definir_senha(conta["aluno_id"], generate_password_hash(senha))
    return _emitir_sessao(conta, momento, ip, "app_aluno_ativacao")


def autenticar_token(token):
    """Resolve o aluno exclusivamente a partir do token. Nunca a partir de parâmetros da requisição."""
    if not token:
        return None
    momento = _texto(agora())
    sessao = AlunoAppRepository.sessao_valida(hash_token(token), momento)
    if sessao:
        AlunoAppRepository.tocar_sessao(sessao["sessao_id"], momento)
    return sessao


def sair(sessao_id, aluno_id, ip):
    AlunoAppRepository.encerrar_sessao(sessao_id)
    log.info("app_aluno_logout aluno_id=%s ip=%s", aluno_id, ip)


# ---- consulta ------------------------------------------------------------

def _status_exibicao(aula, momento):
    if aula["situacao"] != "AGENDADA":
        return aula["situacao"].lower()
    data, hora = momento.date().isoformat(), momento.strftime("%H:%M")
    if aula["data"] > data or (aula["data"] == data and aula["horario_inicio"] > hora):
        return "agendada"
    if aula["data"] == data and aula["horario_fim"] > hora:
        return "em_andamento"
    return "aguardando_registro"


def _duracao(inicio, fim):
    try:
        diferenca = datetime.strptime(fim, "%H:%M") - datetime.strptime(inicio, "%H:%M")
        return int(diferenca.total_seconds() // 60)
    except ValueError:
        return None


def _serializar(aula, momento):
    try:
        dia_semana = DIAS_SEMANA[datetime.strptime(aula["data"], "%Y-%m-%d").weekday()]
    except ValueError:
        dia_semana = None
    return {
        "id": aula["id"],
        "data": aula["data"],
        "dia_semana": dia_semana,
        "horario_inicio": aula["horario_inicio"],
        "horario_fim": aula["horario_fim"],
        "duracao_minutos": _duracao(aula["horario_inicio"], aula["horario_fim"]),
        "categoria": aula["categoria"],
        "situacao": aula["situacao"],
        "status": _status_exibicao(aula, momento),
        "instrutor": {"nome": aula["instrutor_nome"]},
        "veiculo": {"marca": aula["veiculo_marca"], "modelo": aula["veiculo_modelo"], "placa": aula["veiculo_placa"]},
    }


def aulas_do_aluno(aluno_id):
    momento = agora()
    aulas = [_serializar(aula, momento) for aula in AlunoAppRepository.aulas(aluno_id)]
    proximas = [a for a in aulas if a["status"] in ("agendada", "em_andamento")]
    realizadas = [a for a in reversed(aulas) if a["status"] == "realizada"]
    outras = [a for a in reversed(aulas) if a["status"] not in ("agendada", "em_andamento", "realizada")]
    return {"proximas": proximas, "realizadas": realizadas, "outras": outras, "atualizado_em": momento.isoformat(timespec="seconds")}


def contagem(aulas):
    todas = aulas["proximas"] + aulas["realizadas"] + aulas["outras"]
    por_status = defaultdict(int)
    for aula in todas:
        por_status[aula["status"]] += 1
    realizadas = por_status["realizada"]
    agendadas = por_status["agendada"] + por_status["em_andamento"]
    aguardando = por_status["aguardando_registro"]
    na_grade = realizadas + agendadas + aguardando
    return {
        "contratadas": None,
        "na_grade": na_grade,
        "realizadas": realizadas,
        "agendadas": agendadas,
        "aguardando_registro": aguardando,
        "restantes": agendadas + aguardando,
        "faltas": por_status["falta"],
        "canceladas": por_status["cancelada"],
        "reagendadas": por_status["reagendada"],
        "percentual": round(realizadas * 100 / na_grade) if na_grade else 0,
    }


def resumo(aluno_id):
    aulas = aulas_do_aluno(aluno_id)
    perfil = AlunoAppRepository.perfil(aluno_id)
    return {
        "aluno": {"nome": perfil["nome_completo"], "primeiro_nome": perfil["nome_completo"].split()[0]},
        "proxima_aula": aulas["proximas"][0] if aulas["proximas"] else None,
        "contagem": contagem(aulas),
        "atualizado_em": aulas["atualizado_em"],
    }


def aula(aluno_id, aula_id):
    registro = AlunoAppRepository.aula(aluno_id, aula_id)
    return _serializar(registro, agora()) if registro else None


def perfil(aluno_id):
    registro = AlunoAppRepository.perfil(aluno_id)
    return {
        "nome": registro["nome_completo"],
        "cpf": mascarar_cpf(registro["cpf"]),
        "email": registro["email"],
        "categoria_cnh": registro["categoria_cnh"],
        "status": registro["status"],
    }
