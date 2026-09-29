"""Composition root: monta a aplicação e injeta as dependências.

É o único lugar onde as camadas se conhecem — repositórios recebem a conexão,
services recebem repositórios, controllers recebem services, rotas recebem
controllers. Nenhuma camada importa uma instância global de outra.
"""

import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, carregar_env
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.database import schema
from src.database.connection import Database
from src.middlewares import error_handler
from src.repositories.pedido_repository import PedidoRepository
from src.repositories.produto_repository import ProdutoRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.routes import (
    health_routes,
    pedido_routes,
    produto_routes,
    relatorio_routes,
    usuario_routes,
)
from src.services.health_service import HealthService
from src.services.notificacao_service import NotificadorDeLog
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.seguranca import ServicoDeToken
from src.services.usuario_service import UsuarioService


def configurar_logging(nivel):
    logging.basicConfig(
        level=getattr(logging, nivel, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def criar_app(settings=None):
    carregar_env()
    settings = settings or Settings()
    configurar_logging(settings.log_level)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug

    # Default fechado: sem CORS_ORIGINS configurado, nenhuma origem cross-site
    # é liberada (o legado usava `CORS(app)`, equivalente a `*` em toda rota).
    if settings.cors_origins:
        CORS(app, origins=settings.cors_origins)

    database = Database(settings.db_path)
    schema.inicializar(database)

    produto_repository = ProdutoRepository(database)
    usuario_repository = UsuarioRepository(database)
    pedido_repository = PedidoRepository(database)

    servico_de_token = ServicoDeToken(settings.secret_key, settings.token_ttl_segundos)
    notificador = NotificadorDeLog()

    produto_service = ProdutoService(produto_repository)
    usuario_service = UsuarioService(usuario_repository, servico_de_token)
    pedido_service = PedidoService(pedido_repository, produto_repository, notificador)
    relatorio_service = RelatorioService(pedido_repository)
    health_service = HealthService(
        produto_repository, usuario_repository, pedido_repository
    )

    # Disponibilizado ao decorator de auth via `current_app`, evitando um
    # singleton de módulo.
    app.extensions["servico_de_token"] = servico_de_token
    app.extensions["database"] = database

    app.register_blueprint(produto_routes.criar_blueprint(
        ProdutoController(produto_service)))
    app.register_blueprint(usuario_routes.criar_blueprint(
        UsuarioController(usuario_service)))
    app.register_blueprint(pedido_routes.criar_blueprint(
        PedidoController(pedido_service)))
    app.register_blueprint(relatorio_routes.criar_blueprint(
        RelatorioController(relatorio_service)))
    app.register_blueprint(health_routes.criar_blueprint(
        HealthController(health_service)))

    error_handler.registrar(app)

    return app
