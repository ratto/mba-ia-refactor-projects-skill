"""Orquestração HTTP do relatório de vendas."""

from flask import jsonify


class RelatorioController:
    def __init__(self, relatorio_service):
        self._service = relatorio_service

    def vendas(self):
        relatorio = self._service.vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
