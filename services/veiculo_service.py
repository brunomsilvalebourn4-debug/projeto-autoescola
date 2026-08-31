import re
import sqlite3

from repositories.veiculo_repository import VeiculoRepository

STATUS = ("DISPONIVEL", "EM_AULA", "MANUTENCAO", "INATIVO")
CATEGORIAS = ("A", "B", "C", "D", "E")


def salvar_veiculo(form, veiculo_id=None):
    dados = {c: (form.get(c) or "").strip() for c in VeiculoRepository.CAMPOS}
    dados["placa"] = re.sub(r"[^A-Za-z0-9]", "", dados["placa"]).upper()
    dados["categoria"] = dados["categoria"].upper(); dados["status"] = dados["status"].upper() or "DISPONIVEL"
    erros = {}
    if not re.fullmatch(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", dados["placa"]): erros["placa"] = "Informe uma placa válida."
    for campo in ("marca", "modelo", "tipo"):
        if len(dados[campo]) < 2: erros[campo] = f"Informe {campo}."
    try: dados["ano"] = int(dados["ano"]) if dados["ano"] else None
    except ValueError: erros["ano"] = "Informe um ano válido."
    if dados.get("ano") and not 1900 <= dados["ano"] <= 2200: erros["ano"] = "Informe um ano válido."
    if dados["categoria"] not in CATEGORIAS: erros["categoria"] = "Selecione uma categoria válida."
    if dados["status"] not in STATUS: erros["status"] = "Selecione um status válido."
    if erros: return None, dados, erros
    try: veiculo_id = VeiculoRepository.salvar(dados, veiculo_id)
    except sqlite3.IntegrityError:
        erros["placa"] = "Já existe um veículo com esta placa."
        return None, dados, erros
    return veiculo_id, dados, {}
