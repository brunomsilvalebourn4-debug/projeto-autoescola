import re

from models import Aluno
from modules.db import get_connection


class AlunoRepository:
    CAMPOS = (
        "nome_completo", "cpf", "rg", "data_nascimento", "telefone", "whatsapp",
        "email", "cep", "endereco", "numero", "complemento", "bairro", "cidade",
        "uf", "categoria_cnh", "status", "observacoes",
    )

    @staticmethod
    def buscar(aluno_id):
        row = get_connection().execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone()
        return Aluno.from_row(row)

    @staticmethod
    def listar(termo="", status="", pagina=1, por_pagina=10):
        filtros, parametros = [], []
        if termo:
            filtros.append("(nome_completo LIKE ? OR cpf LIKE ? OR telefone LIKE ?)")
            busca = f"%{termo}%"
            busca_numerica = f"%{re.sub(r'\D', '', termo)}%"
            parametros.extend((busca, busca_numerica, busca))
        if status:
            filtros.append("status = ?")
            parametros.append(status)
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        connection = get_connection()
        total = connection.execute(f"SELECT COUNT(*) FROM alunos {where}", parametros).fetchone()[0]
        rows = connection.execute(
            f"SELECT * FROM alunos {where} ORDER BY nome_completo LIMIT ? OFFSET ?",
            (*parametros, por_pagina, (pagina - 1) * por_pagina),
        ).fetchall()
        return [Aluno.from_row(row) for row in rows], total

    @classmethod
    def criar(cls, dados):
        connection = get_connection()
        placeholders = ", ".join("?" for _ in cls.CAMPOS)
        cursor = connection.execute(
            f"INSERT INTO alunos ({', '.join(cls.CAMPOS)}) VALUES ({placeholders})",
            tuple(dados[campo] for campo in cls.CAMPOS),
        )
        connection.commit()
        return cursor.lastrowid

    @classmethod
    def atualizar(cls, aluno_id, dados):
        connection = get_connection()
        assignments = ", ".join(f"{campo} = ?" for campo in cls.CAMPOS)
        connection.execute(
            f"UPDATE alunos SET {assignments}, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
            (*tuple(dados[campo] for campo in cls.CAMPOS), aluno_id),
        )
        connection.commit()
