import re
import sqlite3

from repositories.aluno_repository import AlunoRepository


STATUS = ("ATIVO", "INATIVO", "PROCESSO_CONCLUIDO", "CANCELADO")
CATEGORIAS = ("A", "B", "AB", "C", "D", "E")


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def cpf_valido(cpf):
    cpf = somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[indice]) * (tamanho + 1 - indice) for indice in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            return False
    return True


def validar_formulario(form):
    dados = {campo: (form.get(campo) or "").strip() for campo in AlunoRepository.CAMPOS}
    dados["cpf"] = somente_digitos(dados["cpf"])
    dados["cep"] = somente_digitos(dados["cep"])
    dados["uf"] = dados["uf"].upper()
    dados["categoria_cnh"] = dados["categoria_cnh"].upper()
    dados["status"] = dados["status"].upper() or "ATIVO"
    erros = {}
    if len(dados["nome_completo"]) < 3:
        erros["nome_completo"] = "Informe o nome completo."
    if not cpf_valido(dados["cpf"]):
        erros["cpf"] = "Informe um CPF válido."
    if len(somente_digitos(dados["telefone"])) < 10:
        erros["telefone"] = "Informe um telefone válido."
    if dados["categoria_cnh"] not in CATEGORIAS:
        erros["categoria_cnh"] = "Selecione uma categoria válida."
    if dados["status"] not in STATUS:
        erros["status"] = "Selecione um status válido."
    if dados["uf"] and (len(dados["uf"]) != 2 or not dados["uf"].isalpha()):
        erros["uf"] = "Informe a UF com duas letras."
    if dados["email"] and "@" not in dados["email"]:
        erros["email"] = "Informe um e-mail válido."
    return dados, erros


def salvar(form, aluno_id=None):
    dados, erros = validar_formulario(form)
    if erros:
        return None, dados, erros
    try:
        if aluno_id is None:
            aluno_id = AlunoRepository.criar(dados)
        else:
            AlunoRepository.atualizar(aluno_id, dados)
    except sqlite3.IntegrityError as error:
        if "cpf" in str(error).lower():
            erros["cpf"] = "Já existe um aluno cadastrado com este CPF."
        else:
            erros["geral"] = "Não foi possível salvar o aluno. Verifique os dados."
        return None, dados, erros
    return aluno_id, dados, {}
