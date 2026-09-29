"""Acesso a dados de usuários. Sem regra de negócio, sem HTTP.

Nenhum método deste repositório expõe o hash da senha em resultados destinados
a listagem — `buscar_por_email_com_senha` é o único ponto que o devolve, e
existe exclusivamente para a verificação de login.
"""

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def linha_para_usuario(linha):
    return {campo: linha[campo] for campo in CAMPOS_PUBLICOS}


class UsuarioRepository:
    def __init__(self, database):
        self._db = database

    def listar(self):
        with self._db.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, email, tipo, criado_em FROM usuarios"
            )
            return [linha_para_usuario(linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, usuario_id):
        with self._db.cursor() as cursor:
            cursor.execute(
                "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
                (usuario_id,),
            )
            linha = cursor.fetchone()
        return linha_para_usuario(linha) if linha else None

    def buscar_por_email_com_senha(self, email):
        """Uso restrito à autenticação — devolve também o hash da senha."""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
            linha = cursor.fetchone()
        if not linha:
            return None
        usuario = linha_para_usuario(linha)
        usuario["senha"] = linha["senha"]
        return usuario

    def email_existe(self, email):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
            return cursor.fetchone() is not None

    def criar(self, nome, email, hash_da_senha, tipo="cliente"):
        with self._db.transacao() as cursor:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, hash_da_senha, tipo),
            )
            return cursor.lastrowid

    def contar(self):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            return cursor.fetchone()[0]
