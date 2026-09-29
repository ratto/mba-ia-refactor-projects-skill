"""Mapeamento HTTP da rota raiz e do health check (ambas públicas)."""

from flask import Blueprint


def criar_blueprint(health_controller):
    bp = Blueprint("health", __name__)

    bp.add_url_rule("/", "index", health_controller.index, methods=["GET"])
    bp.add_url_rule(
        "/health", "health_check", health_controller.health_check, methods=["GET"]
    )

    return bp
