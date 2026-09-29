"""Mapeamento HTTP de pedidos."""

from flask import Blueprint

from src.middlewares.auth import requer_admin, requer_autenticacao


def criar_blueprint(pedido_controller):
    bp = Blueprint("pedidos", __name__)

    bp.add_url_rule(
        "/pedidos", "criar_pedido",
        requer_autenticacao(pedido_controller.criar), methods=["POST"],
    )
    bp.add_url_rule(
        "/pedidos", "listar_todos_pedidos",
        requer_admin(pedido_controller.listar_todos), methods=["GET"],
    )
    bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
        requer_autenticacao(pedido_controller.listar_por_usuario), methods=["GET"],
    )
    bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
        requer_admin(pedido_controller.atualizar_status), methods=["PUT"],
    )

    return bp
