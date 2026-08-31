from dataclasses import dataclass, field
from typing import Optional

from .base import RowModel


@dataclass(slots=True)
class Instrutor(RowModel):
    id: Optional[int] = None
    nome: str = ""
    cpf: str = ""
    telefone: str = ""
    email: str = ""
    horario_inicio: str = ""
    horario_fim: str = ""
    ativo: bool = True
    observacoes: str = ""
    categorias: list[str] = field(default_factory=list)
    dias_disponiveis: list[int] = field(default_factory=list)
