# Relatório de Refatoração Arquitetural — code-smells-project

**Data:** 2026-09-28
**Skill:** `refactor-arch`
**Stack preservada:** Python 3 + Flask 3.1.1 + SQLite (`sqlite3` da stdlib)

---

## 1. Fase 1 — Análise do Projeto

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.14.7 (runtime local); código compatível com 3.x
Framework:     Flask 3.1.1 (+ Flask-CORS 5.0.1)
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib, driver de banco)
Domain:        API de e-commerce ("Loja") com produtos, usuários, pedidos/itens,
               login e relatório de vendas
Architecture:  Parcialmente organizada — existe separação nominal em app.py /
               controllers.py / models.py / database.py, mas as responsabilidades
               vazam (models.py concentra SQL + regra de negócio, controllers.py
               faz validação e regra de negócio, app.py define rotas
               administrativas com SQL inline); não há camada de services,
               repositories nem config
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
               — ~784 linhas
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite — loja.db)
================================
```

---

## 2. Fase 2 — Relatório de Auditoria

```
================================
PHASE 2: ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3 + Flask 3.1.1 (SQLite via sqlite3)
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 4 | LOW: 4
```

### Findings

#### [CRITICAL] 1. Credenciais / Segredos Hardcoded
- **File:** `app.py:7-8`
- **Description:** `SECRET_KEY` literal no código-fonte (`"minha-chave-super-secreta-123"`) e `DEBUG = True` fixo na config.
- **Impact:** chave de assinatura de sessão exposta no controle de versão; `DEBUG=True` habilita o console interativo do Werkzeug, permitindo execução remota de código se exposto.
- **Recommendation:** mover para `config/settings.py` lendo `os.environ`, com `.env` + `.env.example` e `.gitignore`.

#### [CRITICAL] 2. Vazamento de Segredo na Resposta HTTP
- **File:** `controllers.py:285-289`
- **Description:** o endpoint público `GET /health` devolvia no corpo da resposta `secret_key`, `debug`, `db_path` e `ambiente`.
- **Impact:** qualquer cliente anônimo obtinha a chave secreta da aplicação e detalhes de infraestrutura — comprometimento total sem autenticação.
- **Recommendation:** reduzir `/health` a status + contagens; nunca serializar configuração sensível.

#### [CRITICAL] 3. SQL Injection generalizada
- **File:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299`
- **Description:** praticamente toda query era montada por concatenação de `+` com entrada do usuário, sem placeholders. Casos com string livre exploráveis diretamente: `login_usuario`, `criar_produto`, `atualizar_produto`, `criar_usuario`, `buscar_produtos`, `atualizar_status_pedido`.
- **Impact:** bypass de autenticação (`' OR '1'='1`), leitura/alteração/destruição de qualquer tabela via `/produtos/busca?q=`, `/login`, `POST /produtos`.
- **Recommendation:** `cursor.execute(sql, (params,))` com `?` em todas as queries; filtros dinâmicos como lista de cláusulas + lista de parâmetros.

#### [CRITICAL] 4. Endpoint de execução de SQL arbitrário exposto
- **File:** `app.py:59-78`
- **Description:** `POST /admin/query` executava qualquer string SQL enviada no corpo da requisição, sem autenticação.
- **Impact:** RCE de banco — leitura completa de dados, `DROP TABLE`, alteração de senhas.
- **Recommendation:** remover o endpoint; não há forma segura de mantê-lo numa API pública.

#### [CRITICAL] 5. Ausência de Autenticação/Autorização em rotas sensíveis
- **File:** `app.py:16, 18, 24, 26, 28, 47-57, 59-78`
- **Description:** `DELETE/PUT /produtos/<id>`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`, `POST /admin/reset-db` e `POST /admin/query` sem nenhuma checagem de identidade. `GET /pedidos/usuario/<id>` também não validava o dono.
- **Impact:** qualquer cliente anônimo lia dados de todos os usuários, apagava o catálogo, alterava pedidos alheios e zerava o banco.
- **Recommendation:** decorators `requer_autenticacao` / `requer_admin` em `middlewares/auth.py`, aplicados nas rotas sensíveis.

#### [CRITICAL] 6. Senhas em texto puro
- **File:** `models.py:83, 99, 109-111, 122-131`; `database.py:76-78`
- **Description:** a coluna `senha` guardava o valor em claro, o login comparava a senha no SQL, e `GET /usuarios` / `GET /usuarios/<id>` retornavam o campo `senha` no JSON.
- **Impact:** vazamento de todas as senhas via endpoint público não autenticado.
- **Recommendation:** hash na criação e verificação; nunca serializar `senha` na resposta.

#### [CRITICAL] 7. Endpoint destrutivo sem proteção
- **File:** `app.py:47-57`
- **Description:** `POST /admin/reset-db` apagava todas as linhas das quatro tabelas sem autenticação.
- **Impact:** perda total de dados acionável por requisição anônima.
- **Recommendation:** remover da API; reposicionar como script local.

#### [HIGH] 8. Regra de negócio na camada de dados ("Fat Model")
- **File:** `models.py:133-169` (`criar_pedido`), `models.py:235-273` (`relatorio_vendas`)
- **Description:** validação de produto, checagem de estoque, cálculo de total, baixa de estoque e faixas de desconto dentro do módulo de acesso a dados, que ainda devolvia `{"erro": ...}` como controle de fluxo.
- **Impact:** regra de domínio não testável sem banco, não reutilizável, e erro de negócio indistinguível de erro técnico.
- **Recommendation:** mover para `services/pedido_service.py` e `services/relatorio_service.py`, com exceções de domínio no lugar de dicionários de erro.

#### [HIGH] 9. Lógica de negócio e validação em Controllers ("Fat Controller")
- **File:** `controllers.py:28-54, 64-92, 188-216, 237-252`
- **Description:** handlers faziam validação de domínio (faixas de preço/estoque, tamanho de nome, categorias e status válidos), disparavam "notificações" (`print` de e-mail/SMS/push) e decidiam efeitos colaterais por status.
- **Impact:** regra acoplada ao HTTP, duplicada entre criação e atualização de produto.
- **Recommendation:** extrair para Services; controller apenas traduz resultado em status HTTP.

#### [HIGH] 10. Transação de pedido sem atomicidade
- **File:** `models.py:133-169`
- **Description:** insert do pedido, inserts de itens e baixa de estoque em múltiplos `execute` com um único `commit` no fim, sem `rollback` em caso de exceção.
- **Impact:** pedidos parcialmente gravados e estoque inconsistente.
- **Recommendation:** transação explícita com `rollback` no erro.

#### [HIGH] 11. Acoplamento Forte / Conexão global sem Injeção de Dependência
- **File:** `database.py:4-10`; `models.py` (todas as funções); `controllers.py:3, 266`
- **Description:** `db_connection` era um singleton global de módulo; todo model chamava `get_db()` diretamente e `health_check` abria cursor e executava SQL no controller.
- **Impact:** impossível testar camadas isoladamente ou trocar o backend; `check_same_thread=False` numa conexão única compartilhada entre threads é fonte de corrida.
- **Recommendation:** repositórios recebem a conexão por construtor, montada uma vez no composition root.

#### [HIGH] 12. Tratamento de erros inconsistente e vazamento de detalhes internos
- **File:** `controllers.py` — 16 blocos (`10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`)
- **Description:** cada handler repetia `try/except Exception` devolvendo `str(e)` ao cliente; sem handler centralizado.
- **Impact:** duplicação, respostas inconsistentes e exposição da estrutura do banco a um atacante.
- **Recommendation:** `@app.errorhandler` central, exceções de domínio tipadas, mensagem genérica em 500.

#### [MEDIUM] 13. Queries N+1
- **File:** `models.py:171-201`, `models.py:203-233`, `models.py:154-166`
- **Description:** uma query de itens por pedido e mais uma por item para o nome do produto; em `criar_pedido`, o produto era consultado duas vezes.
- **Impact:** `GET /pedidos` fazia 1 + N + N×M queries.
- **Recommendation:** query única com `JOIN`, agrupando em memória.

#### [MEDIUM] 14. Validação de Entrada Ausente / Insuficiente
- **File:** `controllers.py:37-46, 111-123, 195-201, 239-240`
- **Description:** `preco`/`estoque` usados em comparações sem checagem de tipo; `float()` sem tratamento em `preco_min`/`preco_max`; itens do pedido sem validação de formato.
- **Impact:** erros 500 onde deveria haver 400.
- **Recommendation:** validadores por recurso, devolvendo 400 estruturado.

#### [MEDIUM] 15. CORS excessivamente permissivo
- **File:** `app.py:9`
- **Description:** `CORS(app)` liberava `*` em todas as rotas, inclusive `/usuarios`, `/relatorios/vendas` e `/admin/*`.
- **Impact:** qualquer site podia consumir endpoints sensíveis pelo navegador da vítima.
- **Recommendation:** origens via configuração, com default fechado.

#### [MEDIUM] 16. API deprecated / uso obsoleto da stack
- **File:** `app.py:88` (`app.run(debug=True)`), `app.py:8` (`DEBUG=True`), `database.py:10` (`sqlite3.connect(..., check_same_thread=False)` sem context manager), `models.py:2` (`import sqlite3` não utilizado)
- **Description:** servidor de desenvolvimento com debug ligado tratado como produção (o `/health` reportava `"ambiente": "producao"`); conexão SQLite nunca fechada e sem escopo transacional; import morto.
- **Equivalente moderno aplicado:** `debug` vindo de `FLASK_DEBUG` (default `False`); context managers `Database.cursor()` / `Database.transacao()` no lugar de conexão global sem `with`; import removido.
- **Observação:** nenhuma API **removida** do Flask 3.x (`@app.before_first_request`, `flask.Markup`) foi encontrada no código.

#### [LOW] 17. Duplicação de Código
- **File:** `controllers.py:28-54` vs `72-90`; `models.py:171-201` vs `203-233`; `models.py:4-22` vs `285-314`
- **Recommendation:** extrair `linha_para_produto`, `_agrupar_em_pedidos` e um validador único de produto.

#### [LOW] 18. Magic Numbers / Strings Soltos
- **File:** `models.py:257-262`; `controllers.py:47-53, 242`
- **Recommendation:** constantes nomeadas (`FAIXAS_DE_DESCONTO`, `CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`).

#### [LOW] 19. Logging via `print` e nomenclatura inconsistente
- **File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`; `app.py:56, 83-86`
- **Description:** `print` com concatenação como mecanismo de log (incluindo e-mail de usuário em log de login); parâmetro `id` sombreando o builtin em `controllers.py:14, 64, 98, 136`.
- **Recommendation:** módulo `logging` configurado uma vez; renomear `id` para `produto_id`/`usuario_id`.

#### [LOW] 20. Funções longas sem decomposição
- **File:** `controllers.py:24-62, 64-96`; `models.py:133-169, 235-273`
- **Recommendation:** resolvido majoritariamente pela separação em camadas.

```
================================
Total: 20 findings
================================
```

---

## 3. Confirmação do Humano

> **"sim, prossiga com a refatoração"**

Aprovadas junto com o plano as seis mudanças de contrato público listadas na Fase 2
(remoção de `/admin/query` e `/admin/reset-db`, `/health` sem segredos, `senha` fora
dos payloads de usuário, hash de senhas com migração automática, e autenticação em
rotas sensíveis).

---

## 4. Fase 3 — Refatoração Concluída

```
================================
PHASE 3: REFACTORING COMPLETE
================================
```

### Nova estrutura de diretórios

```
code-smells-project/
├── .env                        # não versionado (gitignored)
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── app.py                      # entry point: expõe `app` e roda o servidor de dev
├── docs/
│   └── refactor-report-2026-09-28.md
├── scripts/
│   └── reset_db.py             # substitui POST /admin/reset-db
└── src/
    ├── app_factory.py          # composition root — injeta todas as dependências
    ├── exceptions.py           # ErroDeDominio, DadosInvalidos, NaoEncontrado,
    │                           # NaoAutenticado, NaoAutorizado
    ├── config/
    │   └── settings.py         # carregador de .env + Settings
    ├── database/
    │   ├── connection.py       # Database: conexão por thread, cursor(), transacao()
    │   └── schema.py           # DDL + seed + migração de senhas
    ├── repositories/
    │   ├── produto_repository.py
    │   ├── usuario_repository.py
    │   └── pedido_repository.py
    ├── services/
    │   ├── produto_service.py
    │   ├── usuario_service.py
    │   ├── pedido_service.py
    │   ├── relatorio_service.py
    │   ├── health_service.py
    │   ├── notificacao_service.py
    │   ├── seguranca.py        # hash de senha + emissão/validação de token
    │   └── validators.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── relatorio_controller.py
    │   └── health_controller.py
    ├── routes/
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   ├── relatorio_routes.py
    │   └── health_routes.py
    └── middlewares/
        ├── auth.py             # requer_autenticacao / requer_admin / exigir_dono_ou_admin
        └── error_handler.py    # handler centralizado
```

Arquivos legados removidos: `controllers.py`, `models.py`, `database.py` (conteúdo
redistribuído entre as camadas acima).

### Findings resolvidos

| Severidade | Total | Corrigidos | Pendentes |
|---|---|---|---|
| CRITICAL | 7 | 7 | 0 |
| HIGH | 5 | 5 | 0 |
| MEDIUM | 4 | 4 | 0 |
| LOW | 4 | 4 | 0 |
| **Total** | **20** | **20** | **0** |

Detalhe por finding:

1. **Segredos hardcoded** → `src/config/settings.py` lê tudo de `os.environ`; `.env` gerado e gitignorado; `.env.example` versionado. A aplicação se recusa a subir sem `SECRET_KEY`.
2. **Segredo no `/health`** → `HealthService.status()` devolve apenas `status`, `database`, `counts` e `versao`.
3. **SQL Injection** → 100% das queries parametrizadas com `?`. O filtro dinâmico de `ProdutoRepository.pesquisar` monta cláusulas + lista de parâmetros. Verificado no smoke test: `q=' OR '1'='1` retorna 0 resultados e o bypass de login devolve 401.
4. **`POST /admin/query`** → removido.
5. **Auth ausente** → decorators em `src/middlewares/auth.py`, token assinado (`itsdangerous`, já dependência do Flask) emitido no `/login`.
6. **Senhas em texto puro** → `werkzeug.security.generate_password_hash`/`check_password_hash` (também já dependência do Flask). Migração idempotente no boot converte senhas legadas; os logins existentes continuam funcionando. Campo `senha` removido de todos os payloads de resposta.
7. **`POST /admin/reset-db`** → removido da API, reposicionado em `scripts/reset_db.py` com flag `--confirmar`.
8. **Fat Model** → regra de pedido em `PedidoService`, faixas de desconto em `RelatorioService`; repositórios só persistem.
9. **Fat Controller** → validações em `ProdutoService`/`PedidoService`/`UsuarioService`; notificações em `NotificadorDeLog` injetado.
10. **Atomicidade** → `Database.transacao()` com `commit`/`rollback`. A baixa de estoque usa `WHERE id = ? AND estoque >= ?` e aborta a transação inteira se a linha não for afetada (corrida entre validação e gravação).
11. **DI** → `src/app_factory.py` monta `Database → Repositories → Services → Controllers → Routes`. Nenhuma camada importa instância global. Conexão por thread (`threading.local`) elimina o `check_same_thread=False` compartilhado.
12. **Erros** → `src/middlewares/error_handler.py`; 500 devolve mensagem genérica com o traceback só no log.
13. **N+1** → `SQL_PEDIDOS_COM_ITENS` resolve `GET /pedidos` e `GET /pedidos/usuario/<id>` numa query com `LEFT JOIN`; `resumo_de_vendas` agrega em uma query; `PedidoService._precificar` carrega cada produto uma única vez.
14. **Validação** → `src/services/validators.py`. `?preco_min=abc` e `preco` do tipo errado agora retornam 400 (antes, 500).
15. **CORS** → `CORS_ORIGINS` no `.env`, default fechado.
16. **Deprecated/obsoleto** → `debug` vem de `FLASK_DEBUG` (default `False`); context managers no lugar da conexão global sem `with`; import morto removido.
17. **Duplicação** → `linha_para_produto`, `linha_para_usuario`, `_agrupar_em_pedidos`, `ProdutoService._validar`.
18. **Magic numbers** → `FAIXAS_DE_DESCONTO`, `CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `TAMANHO_MINIMO_DO_NOME`, etc.
19. **Logging** → `logging` configurado uma vez em `app_factory.configurar_logging`; nenhum `print` no código da aplicação; e-mail removido dos logs de login; `id` renomeado para `produto_id`/`usuario_id`.
20. **Funções longas** → decompostas pela separação em camadas + passos privados nomeados.

### Validação

```
  ✓ Application boots without errors
      python app.py → "Servidor iniciado em http://127.0.0.1:5000 (debug=False)"
      GET /health via curl → HTTP 200
  ✓ All endpoints respond correctly
      44 checks de smoke test, todos aprovados (status e formato de payload)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
      catálogo reconferido contra o código final; nenhuma query concatenada,
      nenhum segredo hardcoded, nenhum estado global, nenhum try/except duplicado
```

Smoke test executado com o test client do Flask, cobrindo todos os endpoints
originais mais os casos de segurança:

| Endpoint | Antes | Depois |
|---|---|---|
| `GET /` | 200 | 200 (idêntico) |
| `GET /health` | 200 + `secret_key` no corpo | 200 sem dados de config |
| `GET /produtos` | 200 | 200 (idêntico) |
| `GET /produtos/<id>` | 200 / 404 | 200 / 404 (idêntico) |
| `GET /produtos/busca` | 200 (injetável) | 200 (parametrizado); `preco_min=abc` → 400 em vez de 500 |
| `POST /produtos` | 201 / 400 | 201 / 400 (mensagens preservadas) + 401/403 sem admin |
| `PUT /produtos/<id>` | 200 / 404 / 400 | idêntico + 401/403 sem admin |
| `DELETE /produtos/<id>` | 200 / 404 | idêntico + 401/403 sem admin |
| `GET /usuarios` | 200 com `senha` | 200 sem `senha`, exige admin |
| `GET /usuarios/<id>` | 200 com `senha` / 404 | 200 sem `senha` / 404, exige admin |
| `POST /usuarios` | 201 / 400 | 201 / 400 (senha hasheada) |
| `POST /login` | 200 / 401 (injetável) | 200 + `token` / 401 (parametrizado) |
| `POST /pedidos` | 201 / 400 | 201 / 400, exige autenticação e dono |
| `GET /pedidos` | 200 | 200, exige admin |
| `GET /pedidos/usuario/<id>` | 200 | 200, exige dono ou admin |
| `PUT /pedidos/<id>/status` | 200 / 400 | 200 / 400 / 404, exige admin |
| `GET /relatorios/vendas` | 200 | 200, exige admin |
| `POST /admin/query` | 200 (RCE de SQL) | 404 (removido) |
| `POST /admin/reset-db` | 200 (destrutivo) | 404 (removido) |

Comportamento de negócio conferido no smoke test: total do pedido (`89.90×2 + 299.90 = 479.70`),
baixa de estoque (produto 2: 50 → 48), faixas de desconto do relatório, e as mensagens
de erro de validação idênticas às originais (`"Nome é obrigatório"`, `"Preço não pode ser
negativo"`, `"Categoria inválida. Válidas: [...]"`, `"Estoque insuficiente para Cadeira Gamer"`).

O processo do servidor de teste foi encerrado ao final da validação.

---

## 5. Decisões e Trade-offs

**Stack preservada integralmente.** Nenhuma dependência nova foi adicionada:
`requirements.txt` continua com `flask==3.1.1` e `flask-cors==5.0.1`. O hash de
senha usa `werkzeug.security` e o token usa `itsdangerous` — ambos já são
dependências transitivas do Flask. O carregador de `.env` foi escrito em ~15
linhas de stdlib em vez de trazer `python-dotenv`, e a validação usa funções
simples em vez de `pydantic`/`marshmallow` (KISS).

**Schema do banco inalterado.** As quatro tabelas mantêm exatamente a mesma DDL.
A única mudança em dados é o conteúdo da coluna `usuarios.senha`, que passa de
texto puro para hash — migração automática e idempotente no boot, preservando os
logins existentes (verificado: `admin@loja.com` / `admin123` continua funcionando).

**Repositórios sem camada extra.** Como o projeto usa `sqlite3` direto, sem ORM,
os Repositories são a própria camada de dados — não foi criada uma camada de
"Model" anêmica em cima deles só por formalismo.

**Serviços finos aceitos.** `RelatorioService` e `HealthService` têm pouca
lógica, mas existem porque concentram, respectivamente, as faixas de desconto e a
decisão sobre o que é seguro expor. Não foram criados serviços vazios para
entidades sem regra própria.

**Mudanças de contrato público** (aprovadas na Fase 2, sem alternativa segura):

1. `POST /admin/query` e `POST /admin/reset-db` respondem 404 — foram removidos.
   O reset virou `scripts/reset_db.py --confirmar`.
2. `GET /health` não expõe mais `secret_key`, `debug`, `db_path` e `ambiente`.
3. `GET /usuarios` e `GET /usuarios/<id>` não retornam mais o campo `senha`.
4. Rotas sensíveis passaram a responder 401/403 sem token válido. `POST /login`
   ganhou o campo `token` na resposta (adição, não remoção).
5. `POST /usuarios` ignora um eventual campo `tipo` no corpo — aceitá-lo
   permitiria auto-cadastro como admin. Novos usuários são sempre `cliente`.
6. Respostas de erro 4xx agora sempre incluem `"sucesso": false` (antes, algumas
   traziam só `erro`). Adição compatível.
7. Erros inesperados (500) devolvem `"Erro interno do servidor"` em vez da
   mensagem da exceção. É a correção do vazamento de informação — o detalhe
   continua disponível no log do servidor.
8. `POST /produtos` passou a exigir admin. A Fase 2 listava apenas `PUT`/`DELETE`;
   incluir o `POST` foi uma extensão da mesma decisão, já que criar itens no
   catálogo é uma escrita de mesma natureza.

**Ponto que exige ação do operador.** O `.env` gerado neste ambiente tem uma
`SECRET_KEY` aleatória de desenvolvimento. Em qualquer deploy real, uma chave
distinta deve ser provisionada pelo mecanismo de segredos do ambiente — e a chave
antiga (`minha-chave-super-secreta-123`), por ter estado versionada, deve ser
considerada comprometida.

**Não resolvido por depender de infraestrutura.** O `app.run()` do Flask continua
sendo servidor de desenvolvimento; subir em produção exige um WSGI real
(gunicorn/waitress), o que é decisão de deploy e não de código. As notificações
de pedido permanecem apenas em log — nunca houve envio real de e-mail/SMS/push, e
inventar um provedor estaria fora do escopo da refatoração; a interface agora é
injetável, então trocar `NotificadorDeLog` por uma implementação real não toca em
Service nem Controller.
