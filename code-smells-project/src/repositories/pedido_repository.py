"""Acesso a dados de pedidos e itens de pedido. Sem regra de negócio, sem HTTP.

As listagens usam uma única query com JOIN, eliminando o padrão 1 + N + N×M do
código legado (uma query por pedido para os itens, mais uma por item para o nome
do produto).
"""

SQL_PEDIDOS_COM_ITENS = """
    SELECT
        p.id               AS pedido_id,
        p.usuario_id       AS usuario_id,
        p.status           AS status,
        p.total            AS total,
        p.criado_em        AS criado_em,
        i.produto_id       AS produto_id,
        i.quantidade       AS quantidade,
        i.preco_unitario   AS preco_unitario,
        pr.nome            AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr    ON pr.id = i.produto_id
    {filtro}
    ORDER BY p.id, i.id
"""

PRODUTO_DESCONHECIDO = "Desconhecido"


class EstoqueIndisponivel(Exception):
    """Estoque insuficiente detectado dentro da transação de criação do pedido."""

    def __init__(self, produto_id):
        super().__init__(f"Estoque insuficiente para o produto {produto_id}")
        self.produto_id = produto_id


def _agrupar_em_pedidos(linhas):
    """Colapsa o resultado do JOIN em uma lista de pedidos com seus itens."""
    pedidos_por_id = {}
    ordem = []

    for linha in linhas:
        pedido_id = linha["pedido_id"]
        pedido = pedidos_por_id.get(pedido_id)
        if pedido is None:
            pedido = {
                "id": pedido_id,
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            }
            pedidos_por_id[pedido_id] = pedido
            ordem.append(pedido)

        if linha["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] or PRODUTO_DESCONHECIDO,
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })

    return ordem


class PedidoRepository:
    def __init__(self, database):
        self._db = database

    def listar(self):
        with self._db.cursor() as cursor:
            cursor.execute(SQL_PEDIDOS_COM_ITENS.format(filtro=""))
            return _agrupar_em_pedidos(cursor.fetchall())

    def listar_por_usuario(self, usuario_id):
        with self._db.cursor() as cursor:
            cursor.execute(
                SQL_PEDIDOS_COM_ITENS.format(filtro="WHERE p.usuario_id = ?"),
                (usuario_id,),
            )
            return _agrupar_em_pedidos(cursor.fetchall())

    def buscar_por_id(self, pedido_id):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
            linha = cursor.fetchone()
        if not linha:
            return None
        return {
            "id": linha["id"],
            "usuario_id": linha["usuario_id"],
            "status": linha["status"],
            "total": linha["total"],
            "criado_em": linha["criado_em"],
        }

    def criar_com_itens(self, usuario_id, total, itens):
        """Grava pedido + itens + baixa de estoque em uma única transação.

        `itens` são dicts com produto_id, quantidade e preco_unitario, já
        validados e precificados pelo Service.
        """
        with self._db.transacao() as cursor:
            cursor.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, "pendente", total),
            )
            pedido_id = cursor.lastrowid

            cursor.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade,"
                " preco_unitario) VALUES (?, ?, ?, ?)",
                [
                    (pedido_id, item["produto_id"], item["quantidade"],
                     item["preco_unitario"])
                    for item in itens
                ],
            )
            for item in itens:
                # A cláusula `estoque >= ?` revalida dentro da transação: se outro
                # pedido consumiu o estoque entre a validação do Service e aqui,
                # nenhuma linha é afetada e a transação inteira sofre rollback.
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - ?"
                    " WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if cursor.rowcount == 0:
                    raise EstoqueIndisponivel(item["produto_id"])
        return pedido_id

    def atualizar_status(self, pedido_id, novo_status):
        with self._db.transacao() as cursor:
            cursor.execute(
                "UPDATE pedidos SET status = ? WHERE id = ?",
                (novo_status, pedido_id),
            )
            return cursor.rowcount > 0

    def contar(self):
        with self._db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pedidos")
            return cursor.fetchone()[0]

    def resumo_de_vendas(self):
        """Agregados brutos de vendas em uma única query (sem cálculo de negócio)."""
        with self._db.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*)                                            AS total_pedidos,
                    COALESCE(SUM(total), 0)                             AS faturamento,
                    SUM(CASE WHEN status = 'pendente'  THEN 1 ELSE 0 END) AS pendentes,
                    SUM(CASE WHEN status = 'aprovado'  THEN 1 ELSE 0 END) AS aprovados,
                    SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
                FROM pedidos
                """
            )
            linha = cursor.fetchone()

        return {
            "total_pedidos": linha["total_pedidos"],
            "faturamento": linha["faturamento"] or 0,
            "pendentes": linha["pendentes"] or 0,
            "aprovados": linha["aprovados"] or 0,
            "cancelados": linha["cancelados"] or 0,
        }
