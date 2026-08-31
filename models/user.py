from dataclasses import dataclass
from typing import Optional

from .base import RowModel

PERFIS = ("ADMINISTRADOR", "ATENDENTE", "INSTRUTOR")


@dataclass(slots=True)
class User(RowModel):
    id: Optional[int] = None
    nome: str = ""
    email: str = ""
    senha_hash: str = ""
    perfil: str = "ATENDENTE"
    instrutor_id: Optional[int] = None
    ativo: bool = True
