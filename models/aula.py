from dataclasses import dataclass
from typing import Optional

from .base import RowModel

SITUACOES_AULA = ("AGENDADA", "REALIZADA", "CANCELADA", "REAGENDADA", "FALTA")


@dataclass(slots=True)
class Aula(RowModel):
    id: Optional[int] = None
    aluno_id: Optional[int] = None
    instrutor_id: Optional[int] = None
    veiculo_id: Optional[int] = None
    data: str = ""
    horario_inicio: str = ""
    horario_fim: str = ""
    categoria: str = ""
    situacao: str = "AGENDADA"
    observacoes: str = ""
