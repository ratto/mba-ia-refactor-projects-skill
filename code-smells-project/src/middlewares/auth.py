"""Autenticação e autorização como decorators reutilizáveis.

O token é emitido em `POST /login` e enviado no header
`Authorization: Bearer <token>`. A checagem vive num único lugar, em vez de ser
replicada (ou esquecida) em cada handler.
"""

from functools import wraps

from flask import current_app, g, request

from src.exceptions import NaoAutenticado, NaoAutorizado

TIPO_ADMIN = "admin"
PREFIXO_BEARER = "bearer "


def _extrair_token():
    cabecalho = request.headers.get("Authorization", "")
    if cabecalho.lower().startswith(PREFIXO_BEARER):
        return cabecalho[len(PREFIXO_BEARER):].strip()
    return None


def usuario_autenticado():
    """Payload do token da requisição atual, ou None se não autenticado."""
    if "usuario_autenticado" not in g:
        token = _extrair_token()
        servico_de_token = current_app.extensions["servico_de_token"]
        g.usuario_autenticado = servico_de_token.verificar(token) if token else None
    return g.usuario_autenticado


def requer_autenticacao(funcao):
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        if usuario_autenticado() is None:
            raise NaoAutenticado("Autenticação obrigatória")
        return funcao(*args, **kwargs)

    return wrapper


def requer_admin(funcao):
    @wraps(funcao)
    @requer_autenticacao
    def wrapper(*args, **kwargs):
        if usuario_autenticado().get("tipo") != TIPO_ADMIN:
            raise NaoAutorizado("Permissão de administrador obrigatória")
        return funcao(*args, **kwargs)

    return wrapper


def exigir_dono_ou_admin(usuario_id):
    """Garante que o requisitante é o dono do recurso — ou um administrador."""
    autenticado = usuario_autenticado()
    if autenticado is None:
        raise NaoAutenticado("Autenticação obrigatória")
    if autenticado.get("tipo") == TIPO_ADMIN:
        return
    if str(autenticado.get("usuario_id")) != str(usuario_id):
        raise NaoAutorizado("Acesso restrito ao próprio usuário")
