"""Orquestração HTTP de usuários e login. Sem SQL e sem regra de negócio."""

from flask import jsonify, request


class UsuarioController:
    def __init__(self, usuario_service):
        self._service = usuario_service

    def listar(self):
        usuarios = self._service.listar()
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    def buscar(self, usuario_id):
        usuario = self._service.buscar(usuario_id)
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        novo_id = self._service.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201

    def login(self):
        usuario, token = self._service.autenticar(request.get_json(silent=True))
        return jsonify({
            "dados": usuario,
            "token": token,
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200
