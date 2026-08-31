import re

from models import Instrutor
from modules.db import get_connection


class InstrutorRepository:
    CAMPOS = ("nome", "cpf", "telefone", "email", "horario_inicio", "horario_fim", "ativo", "observacoes")

    @staticmethod
    def buscar(instrutor_id):
        connection = get_connection()
        row = connection.execute("SELECT * FROM instrutores WHERE id = ?", (instrutor_id,)).fetchone()
        instrutor = Instrutor.from_row(row)
        if instrutor:
            instrutor.categorias = [r[0] for r in connection.execute("SELECT categoria FROM instrutor_categorias WHERE instrutor_id = ? ORDER BY categoria", (instrutor_id,))]
            instrutor.dias_disponiveis = [r[0] for r in connection.execute("SELECT dia_semana FROM instrutor_disponibilidade WHERE instrutor_id = ? ORDER BY dia_semana", (instrutor_id,))]
        return instrutor

    @staticmethod
    def listar(termo="", ativo="", categoria=""):
        filtros, params = [], []
        if termo:
            filtros.append("(i.nome LIKE ? OR i.cpf LIKE ?)")
            params.extend((f"%{termo}%", f"%{re.sub(r'\D', '', termo)}%"))
        if ativo in ("0", "1"):
            filtros.append("i.ativo = ?")
            params.append(int(ativo))
        if categoria:
            filtros.append("EXISTS (SELECT 1 FROM instrutor_categorias ic WHERE ic.instrutor_id=i.id AND ic.categoria=?)")
            params.append(categoria)
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        return [Instrutor.from_row(r) for r in get_connection().execute(f"SELECT i.* FROM instrutores i {where} ORDER BY i.nome", params)]

    @classmethod
    def salvar(cls, dados, categorias, dias, instrutor_id=None):
        connection = get_connection()
        try:
            if instrutor_id is None:
                cursor = connection.execute(
                    f"INSERT INTO instrutores ({', '.join(cls.CAMPOS)}) VALUES ({', '.join('?' for _ in cls.CAMPOS)})",
                    tuple(dados[c] for c in cls.CAMPOS),
                )
                instrutor_id = cursor.lastrowid
            else:
                connection.execute(
                    f"UPDATE instrutores SET {', '.join(f'{c}=?' for c in cls.CAMPOS)}, atualizado_em=CURRENT_TIMESTAMP WHERE id=?",
                    (*tuple(dados[c] for c in cls.CAMPOS), instrutor_id),
                )
                connection.execute("DELETE FROM instrutor_categorias WHERE instrutor_id=?", (instrutor_id,))
                connection.execute("DELETE FROM instrutor_disponibilidade WHERE instrutor_id=?", (instrutor_id,))
            connection.executemany("INSERT INTO instrutor_categorias VALUES (?, ?)", ((instrutor_id, c) for c in categorias))
            connection.executemany("INSERT INTO instrutor_disponibilidade VALUES (?, ?)", ((instrutor_id, d) for d in dias))
            connection.commit()
            return instrutor_id
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def alternar_ativo(instrutor_id):
        connection = get_connection()
        connection.execute("UPDATE instrutores SET ativo=CASE ativo WHEN 1 THEN 0 ELSE 1 END, atualizado_em=CURRENT_TIMESTAMP WHERE id=?", (instrutor_id,))
        connection.commit()
