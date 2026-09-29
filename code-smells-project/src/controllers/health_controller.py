"""Orquestração HTTP do health check e da rota raiz."""

from flask import jsonify

ENDPOINTS_PUBLICADOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class HealthController:
    def __init__(self, health_service):
        self._service = health_service

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": ENDPOINTS_PUBLICADOS,
        }), 200

    def health_check(self):
        return jsonify(self._service.status()), 200
