from dataclasses import dataclass
from typing import Optional

from .base import RowModel

STATUS_ALUNO = ("ATIVO", "INATIVO", "PROCESSO_CONCLUIDO", "CANCELADO")


@dataclass(slots=True)
class Aluno(RowModel):
    id: Optional[int] = None
    nome_completo: str = ""
    cpf: str = ""
    rg: str = ""
    data_nascimento: str = ""
    telefone: str = ""
    whatsapp: str = ""
    email: str = ""
    cep: str = ""
    endereco: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""
    categoria_cnh: str = ""
    status: str = "ATIVO"
    observacoes: str = ""
