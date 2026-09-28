# Guidelines de Arquitetura Alvo

A skill sempre refatora para o mesmo modelo lógico de camadas, independente da stack. Os nomes de pasta/arquivo se adaptam à convenção idiomática de cada linguagem, mas a **ordem e a responsabilidade de cada camada não mudam**:

```
Request → Views/Routes → Controllers → Services → Models/Repositories → Database
```

## Camadas

### 1. Views / Routes (camada HTTP)
- Responsabilidade única: mapear método+path para uma função de controller, extrair parâmetros de request (path/query/body) e devolver a resposta HTTP produzida pelo controller.
- **Não deve conter:** validação de regra de negócio, SQL, cálculos, formatação de dados complexa.
- Exemplos idiomáticos: `routes/*.py` com Blueprints (Flask), `routes/*.js`/`*.router.js` com `express.Router()` (Express).

### 2. Controllers (orquestração)
- Recebem o que a rota extraiu, validam formato básico de input (ou delegam a um validador/schema), chamam o Service correspondente, e traduzem o resultado/erro do Service em resposta HTTP (status code + corpo).
- **Não deve conter:** SQL/acesso a ORM direto, regra de negócio (cálculo de preço, transição de estado, decisão de domínio).
- Um controller por domínio/recurso (ex.: `produto_controller`, `pedido_controller`), não um controller único para tudo.

### 3. Services (regra de negócio)
- Contêm as regras de domínio: cálculos, validações de negócio, orquestração entre múltiplos repositórios, decisões (ex.: "pedido só pode ser cancelado se status == pendente").
- **Não conhecem HTTP** (sem `request`/`response`, sem status codes) e **não montam SQL bruto** — chamam o Model/Repository para persistência.
- Em projetos pequenos, se uma entidade não tem nenhuma regra de negócio real além de CRUD, um Service "fino" que apenas repassa para o Repository é aceitável (KISS — não force abstração vazia).

### 4. Models / Repositories (acesso a dados)
- Responsáveis por toda a interação com a fonte de dados (ORM, SQL parametrizado, arquivo, cache).
- Expõem métodos de domínio (`find_by_id`, `create`, `list_by_status`), nunca vazam detalhes de conexão para as camadas acima.
- **Não contêm** regra de negócio nem lógica HTTP.
- Se o projeto usa um ORM (SQLAlchemy, Sequelize, Mongoose), o "Model" é a própria classe do ORM; a camada de Repository pode ser o próprio Model quando o ORM já abstrai o acesso — não duplique uma camada de repositório vazia só por formalismo (KISS).

### 5. Middlewares / Cross-cutting
- Tratamento de erro centralizado (um único lugar que captura exceções não tratadas e formata a resposta de erro de forma consistente).
- Autenticação/autorização como middleware/decorator reutilizável, não replicado em cada handler.
- CORS, logging, parsing de body — configurados uma vez, não por rota.

### 6. Config
- Toda credencial/segredo/URL de banco/porta vem de variáveis de ambiente (`.env` + `os.environ`/`process.env`), carregadas em um módulo único de configuração (`config/settings.py`, `config/index.js`). Nunca hardcoded no código de negócio.

### 7. Entry point (composition root)
- Um único arquivo (`app.py`, `main.py`, `server.js`, `app.js`) monta a aplicação: cria a instância do framework, registra middlewares, registra rotas, inicializa configuração — e nada mais. Não deve conter lógica de negócio nem definição de rota inline.

## Exemplos de estrutura de diretórios por stack

### Python/Flask
```
src/
├── config/
│   └── settings.py
├── models/
│   └── produto_model.py
├── repositories/               # opcional se o Model já abstrai o acesso
│   └── produto_repository.py
├── services/
│   └── produto_service.py
├── controllers/
│   └── produto_controller.py
├── routes/
│   └── produto_routes.py
├── middlewares/
│   └── error_handler.py
└── app.py                      # composition root
```

### Node.js/Express
```
src/
├── config/
│   └── index.js
├── models/
│   └── produto.model.js
├── repositories/
│   └── produto.repository.js
├── services/
│   └── produto.service.js
├── controllers/
│   └── produto.controller.js
├── routes/
│   └── produto.routes.js
├── middlewares/
│   └── errorHandler.js
└── app.js                      # composition root
```

Adapte nomes de pasta à convenção que já existir no projeto (ex.: se o projeto já usa `services/`/`routes/` em vez de `controllers/`/`repositories/`, mantenha a convenção existente e apenas corrija as violações de responsabilidade — não renomeie por renomear).

## Validação obrigatória ao final da Fase 3

1. **Boot da aplicação**: iniciar o servidor (comando idiomático da stack — `flask run`, `python app.py`, `node src/app.js`, `npm start`) e confirmar que sobe sem exceção.
2. **Smoke test dos endpoints**: para cada rota que existia antes da refatoração, disparar uma requisição equivalente (via `curl`, script, ou arquivo `.http` já existente no projeto) e confirmar que o status code e o formato da resposta permanecem consistentes com o comportamento anterior.
3. **Zero anti-patterns CRITICAL/HIGH remanescentes**: reconferir o catálogo contra o código final.
4. Encerrar o processo do servidor de teste ao final (não deixar processos pendurados em background sem informar o usuário).
