"""Tratamento de erros centralizado.

Substitui os 16 blocos `try/except Exception` duplicados dos controllers, que
devolviam `str(e)` ao cliente — expondo mensagens de erro do SQLite e a
estrutura interna do banco.

Erros de domínio mantêm a mensagem (ela é para o cliente). Erros inesperados
viram uma resposta 500 genérica, com o detalhe apenas no log do servidor.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.exceptions import ErroDeDominio

logger = logging.getLogger(__name__)

MENSAGEM_DE_ERRO_INTERNO = "Erro interno do servidor"


def registrar(app):
    @app.errorhandler(ErroDeDominio)
    def tratar_erro_de_dominio(erro):
        return jsonify({"erro": str(erro), "sucesso": False}), erro.status_code

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        # 404 de rota inexistente, 405 de método errado, 400 de JSON malformado.
        return jsonify({"erro": erro.description, "sucesso": False}), erro.code

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        logger.exception("Erro não tratado: %s", erro)
        return jsonify({"erro": MENSAGEM_DE_ERRO_INTERNO, "sucesso": False}), 500
