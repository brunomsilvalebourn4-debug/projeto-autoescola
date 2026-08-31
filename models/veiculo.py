from dataclasses import dataclass
from typing import Optional

from .base import RowModel

STATUS_VEICULO = ("DISPONIVEL", "EM_AULA", "MANUTENCAO", "INATIVO")


@dataclass(slots=True)
class Veiculo(RowModel):
    id: Optional[int] = None
    placa: str = ""
    marca: str = ""
    modelo: str = ""
    ano: Optional[int] = None
    categoria: str = ""
    tipo: str = ""
    status: str = "DISPONIVEL"
    observacoes: str = ""
