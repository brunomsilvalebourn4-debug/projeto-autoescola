from dataclasses import dataclass
from typing import Optional

from .base import RowModel

ETAPAS_PADRAO = (
    ("CADASTRO", "Cadastro", 1),
    ("EXAME_MEDICO", "Exame médico", 2),
    ("EXAME_PSICOLOGICO", "Exame psicológico", 3),
    ("CURSO_TEORICO", "Curso teórico", 4),
    ("PROVA_TEORICA", "Prova teórica", 5),
    ("AULAS_PRATICAS", "Aulas práticas", 6),
    ("EXAME_PRATICO", "Exame prático", 7),
    ("CONCLUSAO", "Processo concluído", 8),
)


@dataclass(slots=True)
class ProcessoHabilitacao(RowModel):
    id: Optional[int] = None
    aluno_id: Optional[int] = None
    categoria: str = ""
    status: str = "EM_ANDAMENTO"
    resultado: Optional[str] = None
    data_inicio: str = ""
    data_conclusao: Optional[str] = None
    observacoes: str = ""


@dataclass(slots=True)
class EtapaProcesso(RowModel):
    id: Optional[int] = None
    processo_id: Optional[int] = None
    codigo: str = ""
    nome: str = ""
    ordem: int = 0
    status: str = "NAO_INICIADO"
    data_inicio: Optional[str] = None
    data_conclusao: Optional[str] = None
    observacoes: str = ""
