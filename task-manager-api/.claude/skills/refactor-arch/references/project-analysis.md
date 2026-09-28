# Análise de Projeto — Heurísticas de Detecção

Objetivo: preencher os campos do relatório de Fase 1 (`Language`, `Framework`, `Dependencies`, `Domain`, `Architecture`, `Source files`, `DB tables`) de forma confiável, sem assumir a stack de antemão.

## 1. Detecção de linguagem

Olhe primeiro para arquivos de manifesto/build na raiz do projeto — eles são mais confiáveis que extensões de arquivo:

| Sinal encontrado | Linguagem |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py` | Python |
| `package.json` | Node.js / JavaScript ou TypeScript (`"type": "module"`, `tsconfig.json` → TS) |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `go.mod` | Go |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# / .NET |

Se houver ambiguidade (ex.: múltiplos manifestos), confirme pela extensão predominante dos arquivos-fonte (`*.py`, `*.js`, `*.ts`, etc.) contando arquivos fora de pastas de dependências/build.

## 2. Detecção de framework e versão

- **Python**: leia `requirements.txt`/`pyproject.toml` procurando `flask`, `fastapi`, `django`, `bottle`, etc. A versão vem do pin (`Flask==3.1.1`). Confirme no código: `from flask import Flask` + `app = Flask(__name__)`, `@app.route(...)`.
- **Node.js**: leia `package.json` → `dependencies`/`devDependencies` procurando `express`, `fastify`, `koa`, `@nestjs/core`, etc. Versão vem do campo do pacote. Confirme no código: `require('express')` ou `import express from 'express'`, `app.get(...)`.
- Se não houver framework web explícito, classifique como "framework-less" (uso direto de `http`/`wsgi`/etc.) e descreva.

## 3. Dependências relevantes

Liste apenas dependências que impactam a arquitetura ou a auditoria: framework web, driver/ORM de banco (`sqlite3`, `sequelize`, `sqlalchemy`, `mongoose`, `pg`), middlewares de segurança (`flask-cors`, `cors`, `helmet`), autenticação (`jsonwebtoken`, `flask-jwt-extended`, `bcrypt`), validação (`joi`, `zod`, `pydantic`, `marshmallow`). Ignore dependências de dev/test irrelevantes para a arquitetura.

## 4. Detecção de banco de dados

- Procure strings de conexão, imports de driver (`sqlite3`, `psycopg2`, `pymongo`, `mysql.connector`, `pg`, `mongoose.connect`), ou arquivos `.db`/`.sqlite` no repositório.
- Para SQL: extraia nomes de tabelas de `CREATE TABLE`, de chamadas ORM (`class Produto(db.Model)`, `sequelize.define('Produto', ...)`) ou de queries (`SELECT * FROM produtos`).
- Para NoSQL: extraia nomes de coleções/schemas (`mongoose.Schema`, `db.collection('pedidos')`).
- Se não houver banco persistente (dados em memória, array/dict global), registre isso explicitamente — é também um anti-pattern (ver catálogo, "Estado Global Mutável").

## 5. Detecção de domínio da aplicação

Leia os nomes de rotas, modelos e variáveis (em português ou inglês) para inferir o domínio de negócio em 1 frase (ex.: "E-commerce API (produtos, pedidos, usuários)", "LMS API com fluxo de checkout", "Task Manager API"). Não invente — baseie-se em nomes reais de entidades/rotas encontrados no código.

## 6. Mapeamento da arquitetura atual

Classifique em uma das categorias (ou descreva a intermediária):

- **Monolítica sem camadas**: toda a lógica (rotas + regras de negócio + acesso a dados) concentrada em 1-4 arquivos na raiz, sem pastas `models/`, `controllers/`, `routes/`, `services/`.
- **Parcialmente organizada**: já existem algumas pastas por responsabilidade (`models/`, `routes/`, `services/`, `utils/`), mas a separação é inconsistente — regras de negócio vazam para rotas, models fazem query direta sem repositório, ou existe acoplamento cruzado entre camadas.
- **MVC bem aplicado**: camadas claramente separadas, dependências fluindo em uma direção (routes → controllers → services → models), sem violações relevantes. (Raro em projetos legados — se encontrar isso, a Fase 2 deve refletir poucos findings.)

Para chegar à classificação, verifique:
1. Existe uma pasta/arquivo por responsabilidade, ou tudo está em 1-2 arquivos gigantes?
2. As rotas chamam controllers, ou executam lógica de negócio e SQL diretamente no handler?
3. Existe alguma forma de injeção de dependência ou tudo importa instâncias globais (conexão de banco, app) diretamente?

## 7. Contagem de arquivos e linhas

Conte apenas arquivos de código-fonte da aplicação (exclua dependências, testes gerados, caches, bancos `.db`, `node_modules`, `__pycache__`, `venv`, `.git`, `instance/`). Registre o número total de arquivos analisados e uma estimativa de linhas de código (soma de linhas dos arquivos-fonte).

## Saída esperada da Fase 1

Preencha exatamente os campos do template em `report-template.md`, seção "PHASE 1". Não adicione seções extras nesta fase — o detalhamento de problemas é exclusivo da Fase 2.
