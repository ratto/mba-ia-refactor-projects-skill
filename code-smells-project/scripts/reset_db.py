"""Limpa todas as tabelas do banco e reaplica o seed inicial.

Substitui o endpoint `POST /admin/reset-db`, que permitia a qualquer cliente
anônimo apagar o banco inteiro. Como script local, exige acesso ao servidor e
confirmação explícita.

Uso:
    python scripts/reset_db.py --confirmar
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import Settings, carregar_env  # noqa: E402
from src.database import schema  # noqa: E402
from src.database.connection import Database  # noqa: E402

TABELAS_NA_ORDEM_DE_EXCLUSAO = ("itens_pedido", "pedidos", "produtos", "usuarios")


def main():
    if "--confirmar" not in sys.argv:
        print("Esta operação apaga TODOS os dados. Rode novamente com --confirmar.")
        return 1

    carregar_env()
    settings = Settings()
    database = Database(settings.db_path)

    schema.inicializar(database)
    with database.transacao() as cursor:
        for tabela in TABELAS_NA_ORDEM_DE_EXCLUSAO:
            cursor.execute(f"DELETE FROM {tabela}")

    schema.inicializar(database)
    database.fechar()
    print(f"Banco resetado: {settings.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
