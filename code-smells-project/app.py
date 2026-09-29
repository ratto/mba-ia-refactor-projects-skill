"""Ponto de entrada da API da Loja.

Toda a montagem da aplicação vive em `src/app_factory.py`. Este arquivo apenas
expõe a instância `app` (para `flask run` / WSGI) e roda o servidor de
desenvolvimento quando executado diretamente.
"""

import logging

from src.app_factory import criar_app
from src.config.settings import Settings, carregar_env

carregar_env()
settings = Settings()
app = criar_app(settings)

if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Servidor iniciado em http://%s:%s (debug=%s)",
        settings.host, settings.port, settings.debug,
    )
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
