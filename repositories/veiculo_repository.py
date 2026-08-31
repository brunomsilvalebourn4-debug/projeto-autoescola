from models import Veiculo
from modules.db import get_connection


class VeiculoRepository:
    CAMPOS = ("placa", "marca", "modelo", "ano", "categoria", "tipo", "status", "observacoes")

    @staticmethod
    def buscar(veiculo_id):
        return Veiculo.from_row(get_connection().execute("SELECT * FROM veiculos WHERE id=?", (veiculo_id,)).fetchone())

    @staticmethod
    def listar(termo="", status="", categoria=""):
        filtros, params = [], []
        if termo:
            filtros.append("(placa LIKE ? OR marca LIKE ? OR modelo LIKE ?)")
            params.extend((f"%{termo}%",) * 3)
        if status:
            filtros.append("status=?"); params.append(status)
        if categoria:
            filtros.append("categoria=?"); params.append(categoria)
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        return [Veiculo.from_row(r) for r in get_connection().execute(f"SELECT * FROM veiculos {where} ORDER BY placa", params)]

    @classmethod
    def salvar(cls, dados, veiculo_id=None):
        connection = get_connection()
        if veiculo_id is None:
            cursor = connection.execute(f"INSERT INTO veiculos ({', '.join(cls.CAMPOS)}) VALUES ({', '.join('?' for _ in cls.CAMPOS)})", tuple(dados[c] for c in cls.CAMPOS))
            veiculo_id = cursor.lastrowid
        else:
            connection.execute(f"UPDATE veiculos SET {', '.join(f'{c}=?' for c in cls.CAMPOS)}, atualizado_em=CURRENT_TIMESTAMP WHERE id=?", (*tuple(dados[c] for c in cls.CAMPOS), veiculo_id))
        connection.commit()
        return veiculo_id
