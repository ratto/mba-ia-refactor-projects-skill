"""Mapeamento HTTP de usuários e login."""

from flask import Blueprint

from src.middlewares.auth import requer_admin


def criar_blueprint(usuario_controller):
    bp = Blueprint("usuarios", __name__)

    bp.add_url_rule(
        "/usuarios", "listar_usuarios",
        requer_admin(usuario_controller.listar), methods=["GET"],
    )
    bp.add_url_rule(
        "/usuarios/<int:usuario_id>", "buscar_usuario",
        requer_admin(usuario_controller.buscar), methods=["GET"],
    )
    bp.add_url_rule(
        "/usuarios", "criar_usuario",
        usuario_controller.criar, methods=["POST"],
    )
    bp.add_url_rule(
        "/login", "login",
        usuario_controller.login, methods=["POST"],
    )

    return bp
