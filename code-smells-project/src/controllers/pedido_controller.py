"""Orquestração HTTP de pedidos. Sem SQL e sem regra de negócio."""

from flask import jsonify, request

from src.middlewares.auth import exigir_dono_ou_admin


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def listar_todos(self):
        pedidos = self._service.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        exigir_dono_ou_admin(usuario_id)
        pedidos = self._service.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True) or {}
        # Um cliente autenticado só cria pedido para si mesmo; admin cria para
        # qualquer usuário.
        if dados.get("usuario_id"):
            exigir_dono_ou_admin(dados["usuario_id"])

        resultado = self._service.criar(dados)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def atualizar_status(self, pedido_id):
        self._service.atualizar_status(pedido_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
