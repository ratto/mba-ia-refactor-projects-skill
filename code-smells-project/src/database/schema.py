"""Criação do schema, seed inicial e migração de senhas em texto puro.

O schema das quatro tabelas originais é preservado byte a byte — a refatoração
não altera a estrutura do banco. A única mudança nos dados é o conteúdo da
coluna `usuarios.senha`, que passa a guardar um hash em vez do texto puro.
"""

import logging

from src.services.seguranca import gerar_hash_senha, parece_hash

logger = logging.getLogger(__name__)

TABELAS = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

PRODUTOS_SEED = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]


def inicializar(database):
    """Cria as tabelas, popula o seed inicial e migra senhas legadas."""
    with database.transacao() as cursor:
        for ddl in TABELAS:
            cursor.execute(ddl)

    _popular_seed(database)
    migrar_senhas_em_texto_puro(database)


def _popular_seed(database):
    with database.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] != 0:
            return

    with database.transacao() as cursor:
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
            " VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_SEED,
        )
        cursor.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [
                (nome, email, gerar_hash_senha(senha), tipo)
                for nome, email, senha, tipo in USUARIOS_SEED
            ],
        )
    logger.info("Seed inicial aplicado (%d produtos, %d usuários)",
                len(PRODUTOS_SEED), len(USUARIOS_SEED))


def migrar_senhas_em_texto_puro(database):
    """Converte senhas legadas em texto puro para hash, preservando o login.

    Bancos criados pela versão anterior guardavam a senha em claro. A migração
    é idempotente: quem já está em hash é ignorado.
    """
    with database.cursor() as cursor:
        cursor.execute("SELECT id, senha FROM usuarios")
        pendentes = [
            (linha["id"], linha["senha"])
            for linha in cursor.fetchall()
            if linha["senha"] and not parece_hash(linha["senha"])
        ]

    if not pendentes:
        return

    with database.transacao() as cursor:
        cursor.executemany(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            [(gerar_hash_senha(senha), usuario_id) for usuario_id, senha in pendentes],
        )
    logger.warning("Migradas %d senha(s) de texto puro para hash", len(pendentes))
