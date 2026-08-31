from modules.db import get_connection


class UserRepository:
    @staticmethod
    def listar():
        return get_connection().execute("SELECT u.*,i.nome instrutor_nome FROM users u LEFT JOIN instrutores i ON i.id=u.instrutor_id ORDER BY u.nome").fetchall()

    @staticmethod
    def buscar(user_id):
        return get_connection().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    @staticmethod
    def instrutores():
        return get_connection().execute("SELECT id,nome FROM instrutores WHERE ativo=1 ORDER BY nome").fetchall()

    @staticmethod
    def salvar(dados, user_id=None):
        connection = get_connection()
        if user_id is None:
            user_id = connection.execute("INSERT INTO users(nome,email,senha_hash,perfil,instrutor_id,ativo) VALUES(?,?,?,?,?,?)", (dados["nome"],dados["email"],dados["senha_hash"],dados["perfil"],dados["instrutor_id"],dados["ativo"])).lastrowid
        else:
            campos=[dados["nome"],dados["email"],dados["perfil"],dados["instrutor_id"],dados["ativo"]]
            sql="UPDATE users SET nome=?,email=?,perfil=?,instrutor_id=?,ativo=?,atualizado_em=CURRENT_TIMESTAMP"
            if dados.get("senha_hash"):
                sql+=",senha_hash=?";campos.append(dados["senha_hash"])
            campos.append(user_id);connection.execute(sql+" WHERE id=?",campos)
        connection.commit();return user_id
