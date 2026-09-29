"""Orquestração HTTP de produtos: extrai o input, chama o Service, formata a
resposta. Sem SQL e sem regra de negócio.

Não há `try/except` aqui — erros de domínio sobem como exceção e são traduzidos
em status HTTP pelo handler central.
"""

from flask import jsonify, request


class ProdutoController:
    def __init__(self, produto_service):
        self._service = produto_service

    def listar(self):
        produtos = self._service.listar()
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar(self, produto_id):
        produto = self._service.buscar(produto_id)
        return jsonify({"dados": produto, "sucesso": True}), 200

    def pesquisar(self):
        resultados = self._service.pesquisar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=request.args.get("preco_min"),
            preco_max=request.args.get("preco_max"),
        )
        return jsonify({
            "dados": resultados,
            "total": len(resultados),
            "sucesso": True,
        }), 200

    def criar(self):
        produto_id = self._service.criar(request.get_json(silent=True))
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, produto_id):
        self._service.atualizar(produto_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self._service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
