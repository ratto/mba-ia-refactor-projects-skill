"""Notificações de pedido.

No código legado isto eram `print`s espalhados pelos controllers. A
implementação continua sendo apenas registro em log — não havia nenhum envio
real de e-mail/SMS/push —, mas agora é uma dependência injetável, o que permite
substituí-la por um provedor real sem tocar em Service ou Controller.
"""

import logging

logger = logging.getLogger(__name__)


class NotificadorDeLog:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("EMAIL: pedido %s criado para o usuário %s", pedido_id, usuario_id)
        logger.info("SMS: seu pedido foi recebido")
        logger.info("PUSH: novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, novo_status):
        logger.info("Pedido %s teve o status alterado para %s", pedido_id, novo_status)
