"""Mapeamento HTTP de relatórios."""

from flask import Blueprint

from src.middlewares.auth import requer_admin


def criar_blueprint(relatorio_controller):
    bp = Blueprint("relatorios", __name__)

    bp.add_url_rule(
        "/relatorios/vendas", "relatorio_vendas",
        requer_admin(relatorio_controller.vendas), methods=["GET"],
    )

    return bp
