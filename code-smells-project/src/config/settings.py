"""Configuração da aplicação — toda ela vinda de variáveis de ambiente.

Nenhum segredo pode ser escrito neste arquivo. O carregamento do `.env` é feito
com a stdlib para não introduzir uma dependência nova só para isso (KISS).
"""

import os
from pathlib import Path

RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]


def carregar_env(caminho=None):
    """Carrega pares CHAVE=valor de um arquivo .env para os.environ.

    Variáveis já presentes no ambiente têm precedência sobre o arquivo.
    """
    caminho = Path(caminho or RAIZ_DO_PROJETO / ".env")
    if not caminho.is_file():
        return

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip("'\"")
        os.environ.setdefault(chave, valor)


def _booleano(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "on", "sim")


class Settings:
    """Snapshot imutável da configuração, montado uma vez no composition root."""

    def __init__(self):
        self.secret_key = os.environ.get("SECRET_KEY")
        if not self.secret_key:
            raise RuntimeError(
                "SECRET_KEY não definida. Copie .env.example para .env e defina um valor."
            )

        self.debug = _booleano("FLASK_DEBUG", padrao=False)
        self.host = os.environ.get("HOST", "127.0.0.1")
        self.port = int(os.environ.get("PORT", "5000"))

        db_path = os.environ.get("DB_PATH", "loja.db")
        self.db_path = str(Path(db_path) if Path(db_path).is_absolute()
                           else RAIZ_DO_PROJETO / db_path)

        origens = os.environ.get("CORS_ORIGINS", "").strip()
        # Default fechado: sem CORS_ORIGINS, nenhuma origem cross-site é liberada.
        self.cors_origins = [o.strip() for o in origens.split(",") if o.strip()]

        self.token_ttl_segundos = int(os.environ.get("TOKEN_TTL_SEGUNDOS", "86400"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
