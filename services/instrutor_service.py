import sqlite3

from repositories.instrutor_repository import InstrutorRepository
from services.aluno_service import cpf_valido, somente_digitos

CATEGORIAS = ("A", "B", "AB", "C", "D", "E")
DIAS = ((0, "Segunda"), (1, "Terça"), (2, "Quarta"), (3, "Quinta"), (4, "Sexta"), (5, "Sábado"), (6, "Domingo"))


def salvar_instrutor(form, instrutor_id=None):
    dados = {c: (form.get(c) or "").strip() for c in InstrutorRepository.CAMPOS}
    dados["cpf"] = somente_digitos(dados["cpf"])
    dados["ativo"] = 1 if form.get("ativo", "1") == "1" else 0
    categorias = sorted(set(form.getlist("categorias")))
    dias = sorted({int(d) for d in form.getlist("dias") if d.isdigit() and 0 <= int(d) <= 6})
    erros = {}
    if len(dados["nome"]) < 3: erros["nome"] = "Informe o nome completo."
    if not cpf_valido(dados["cpf"]): erros["cpf"] = "Informe um CPF válido."
    if len(somente_digitos(dados["telefone"])) < 10: erros["telefone"] = "Informe um telefone válido."
    if not categorias or any(c not in CATEGORIAS for c in categorias): erros["categorias"] = "Selecione ao menos uma categoria válida."
    if not dias: erros["dias"] = "Selecione ao menos um dia disponível."
    if not dados["horario_inicio"] or not dados["horario_fim"] or dados["horario_inicio"] >= dados["horario_fim"]: erros["horarios"] = "Informe um horário inicial anterior ao final."
    if dados["email"] and "@" not in dados["email"]: erros["email"] = "Informe um e-mail válido."
    if erros: return None, dados, categorias, dias, erros
    try:
        instrutor_id = InstrutorRepository.salvar(dados, categorias, dias, instrutor_id)
    except sqlite3.IntegrityError:
        erros["cpf"] = "Já existe um instrutor com este CPF."
        return None, dados, categorias, dias, erros
    return instrutor_id, dados, categorias, dias, {}
