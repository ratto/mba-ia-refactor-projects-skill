"""Verificação de saúde da aplicação.

A versão anterior devolvia `secret_key`, `debug`, `db_path` e `ambiente` no
corpo da resposta de um endpoint público. Aqui o payload se restringe a status e
contagens — nenhum dado de configuração é serializado.
"""

VERSAO_DA_API = "1.0.0"


class HealthService:
    def __init__(self, produto_repository, usuario_repository, pedido_repository):
        self._produtos = produto_repository
        self._usuarios = usuario_repository
        self._pedidos = pedido_repository

    def status(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": VERSAO_DA_API,
        }
