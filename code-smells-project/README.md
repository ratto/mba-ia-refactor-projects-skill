# code-smells-project

API de E-commerce em Python/Flask, refatorada para arquitetura MVC em camadas
(`routes → controllers → services → repositories`).

## Como rodar

```bash
pip install -r requirements.txt

# 1. Crie o .env a partir do template e gere uma SECRET_KEY:
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # cole em SECRET_KEY

# 2. Suba a aplicação:
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo.

`SECRET_KEY` é obrigatória — a aplicação se recusa a subir sem ela. Todas as
demais configurações (porta, host, debug, caminho do banco, origens de CORS)
também vêm do `.env`; veja `.env.example`.

## Autenticação

Rotas sensíveis exigem um token obtido em `POST /login`:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@loja.com","senha":"admin123"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl http://127.0.0.1:5000/usuarios -H "Authorization: Bearer $TOKEN"
```

| Acesso | Rotas |
|---|---|
| Público | `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /usuarios`, `POST /login` |
| Autenticado | `POST /pedidos`, `GET /pedidos/usuario/<id>` (dono ou admin) |
| Admin | `POST/PUT/DELETE /produtos`, `GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas` |

## Estrutura

```
app.py                  # entry point — expõe `app` e roda o servidor de dev
src/
├── app_factory.py      # composition root: monta e injeta as dependências
├── config/settings.py  # configuração vinda de variáveis de ambiente
├── database/           # conexão SQLite + schema/seed/migração
├── repositories/       # acesso a dados (SQL parametrizado)
├── services/           # regra de negócio
├── controllers/        # orquestração HTTP
├── routes/             # mapeamento de path/verbo (blueprints)
├── middlewares/        # auth e tratamento de erro centralizado
└── exceptions.py       # exceções de domínio
scripts/reset_db.py     # limpeza do banco (substitui o antigo POST /admin/reset-db)
docs/                   # relatório da refatoração
```

## Manutenção do banco

```bash
python scripts/reset_db.py --confirmar   # apaga todos os dados e reaplica o seed
```
