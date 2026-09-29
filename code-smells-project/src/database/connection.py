"""Fábrica de conexões SQLite.

Substitui o singleton global de módulo do código legado. A instância é criada
uma única vez no composition root e injetada nos repositórios, que nunca
importam a conexão diretamente.

Cada thread recebe sua própria conexão (`threading.local`), o que remove a
condição de corrida do `check_same_thread=False` sobre uma conexão única
compartilhada por todas as threads do servidor.
"""

import sqlite3
import threading
from contextlib import contextmanager


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()

    def conexao(self):
        """Conexão dedicada à thread atual, criada sob demanda."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
        return conn

    @contextmanager
    def cursor(self):
        """Cursor somente-leitura — não confirma nada."""
        cur = self.conexao().cursor()
        try:
            yield cur
        finally:
            cur.close()

    @contextmanager
    def transacao(self):
        """Escrita atômica: commit no sucesso, rollback em qualquer exceção."""
        conn = self.conexao()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def fechar(self):
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
