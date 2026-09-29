"""Acesso a dados de produtos. Sem regra de negócio, sem HTTP."""

CAMPOS_DO_PRODUTO = (
    "id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em",
)


def linha_para_produto(linha):
    return {campo: linha[campo] for campo in CAMPOS_DO_PRODUTO}


class ProdutoRepository:
    def __init__(self, database):
        self._db = database

    def listar(self):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM produtos")
            return [linha_para_produto(linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, produto_id):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
            linha = cursor.fetchone()
        return linha_para_produto(linha) if linha else None

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Filtro dinâmico montado como cláusulas + parâmetros posicionais."""
        clausulas = ["1=1"]
        parametros = []

        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            curinga = f"%{termo}%"
            parametros.extend([curinga, curinga])
        if categoria:
            clausulas.append("categoria = ?")
            parametros.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            parametros.append(preco_max)

        sql = "SELECT * FROM produtos WHERE " + " AND ".join(clausulas)
        with self._db.cursor() as cursor:
            cursor.execute(sql, parametros)
            return [linha_para_produto(linha) for linha in cursor.fetchall()]

    def criar(self, nome, descricao, preco, estoque, categoria):
        with self._db.transacao() as cursor:
            cursor.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
                " VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
            return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        with self._db.transacao() as cursor:
            cursor.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?,"
                " estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )
            return cursor.rowcount > 0

    def deletar(self, produto_id):
        with self._db.transacao() as cursor:
            cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            return cursor.rowcount > 0

    def contar(self):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM produtos")
            return cursor.fetchone()[0]
