"""Exceções de domínio.

Os Services levantam estas exceções; o handler de erro central (middlewares/
error_handler.py) é o único lugar que as traduz em status HTTP. Nenhuma camada
abaixo de Controllers conhece códigos HTTP diretamente.
"""


class ErroDeDominio(Exception):
    """Falha de regra de negócio — o cliente enviou algo inválido."""

    status_code = 400


class DadosInvalidos(ErroDeDominio):
    status_code = 400


class NaoEncontrado(ErroDeDominio):
    status_code = 404


class NaoAutenticado(ErroDeDominio):
    status_code = 401


class NaoAutorizado(ErroDeDominio):
    status_code = 403
