"""Mapeamento HTTP de produtos. Só path, verbo e delegação ao controller."""

from flask import Blueprint

from src.middlewares.auth import requer_admin


def criar_blueprint(produto_controller):
    bp = Blueprint("produtos", __name__)

    bp.add_url_rule(
        "/produtos", "listar_produtos",
        produto_controller.listar, methods=["GET"],
    )
    bp.add_url_rule(
        "/produtos/busca", "buscar_produtos",
        produto_controller.pesquisar, methods=["GET"],
    )
    bp.add_url_rule(
        "/produtos/<int:produto_id>", "buscar_produto",
        produto_controller.buscar, methods=["GET"],
    )
    bp.add_url_rule(
        "/produtos", "criar_produto",
        requer_admin(produto_controller.criar), methods=["POST"],
    )
    bp.add_url_rule(
        "/produtos/<int:produto_id>", "atualizar_produto",
        requer_admin(produto_controller.atualizar), methods=["PUT"],
    )
    bp.add_url_rule(
        "/produtos/<int:produto_id>", "deletar_produto",
        requer_admin(produto_controller.deletar), methods=["DELETE"],
    )

    return bp
