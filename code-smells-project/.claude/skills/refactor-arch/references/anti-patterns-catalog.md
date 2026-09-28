# Catálogo de Anti-Patterns

Para cada anti-pattern abaixo: **sinais de detecção** (o que procurar no código, agnóstico de stack) e **severidade**. Use isto na Fase 2 para gerar findings com arquivo/linha exatos. A lista cobre Python/Flask e Node/Express como exemplos, mas os sinais são generalizáveis a qualquer stack de API.

---

## CRITICAL

### 1. Credenciais / Segredos Hardcoded
**Sinais de detecção:** literais de string atribuídos a variáveis como `SECRET_KEY`, `API_KEY`, `PASSWORD`, `TOKEN`, `DB_PASSWORD`, connection strings com usuário/senha embutidos, chaves JWT hardcoded no código-fonte (não em `.env`/variável de ambiente).
**Impacto:** exposição de credenciais no controle de versão; qualquer pessoa com acesso ao repositório compromete produção.
**Exemplo de sinal:** `app.config['SECRET_KEY'] = 'minha-chave-super-secreta-123'` ou `const JWT_SECRET = "senha123"`.

### 2. SQL Injection
**Sinais de detecção:** montagem de query via f-string, `.format()`, concatenação `+`, ou template strings diretamente com input do usuário, em vez de placeholders parametrizados (`?`, `%s`, prepared statements, ORM query builder).
**Impacto:** execução arbitrária de SQL, vazamento/alteração/destruição de dados.
**Exemplo de sinal:** `f"SELECT * FROM usuarios WHERE id = {user_id}"` ou `` `SELECT * FROM users WHERE email = '${email}'` ``.

### 3. God Class / God File
**Sinais de detecção:** um único arquivo concentra definição de rotas + lógica de negócio + acesso direto ao banco (SQL/ORM) + validação + formatação de resposta, para múltiplos domínios de negócio diferentes. Geralmente 200+ linhas misturando responsabilidades sem nenhuma função auxiliar isolada.
**Impacto:** impossível testar em isolamento; qualquer mudança tem alto risco de efeito colateral em funcionalidades não relacionadas.
**Exemplo de sinal:** `models.py` ou `app.py` com classes/funções para produtos, pedidos e usuários todas no mesmo arquivo, cada uma abrindo sua própria conexão de banco e fazendo sua própria validação.

### 4. Ausência de Autenticação/Autorização em Rotas Sensíveis
**Sinais de detecção:** rotas que alteram ou expõem dados sensíveis (`DELETE`, `PUT`, listagem de usuários, dados de pagamento/checkout) sem nenhuma checagem de identidade/permissão antes de executar a ação.
**Impacto:** qualquer cliente não autenticado pode ler ou alterar dados de outros usuários.
**Exemplo de sinal:** rota `@app.route('/usuarios/<id>', methods=['DELETE'])` sem decorator/middleware de auth e sem verificar se o requisitante é dono do recurso.

---

## HIGH

### 5. Lógica de Negócio em Controllers/Rotas ("Fat Controller")
**Sinais de detecção:** handler de rota contém cálculos de regra de negócio (descontos, totais, transições de estado, validações de domínio complexas) em vez de delegar a uma camada de serviço.
**Impacto:** regra de negócio não é reutilizável nem testável isoladamente da camada HTTP.
**Exemplo de sinal:** dentro de `def criar_pedido():`, cálculo de frete/desconto/estoque feito inline, misturado com `request.json` e `return jsonify(...)`.

### 6. Acoplamento Forte / Ausência de Injeção de Dependência
**Sinais de detecção:** módulos importam e instanciam diretamente conexões de banco, clients externos ou singletons globais em vez de recebê-los como parâmetro/dependência; impossível substituir por um mock em teste sem alterar o código-fonte.
**Impacto:** dificulta testes unitários e troca de implementação (ex.: trocar SQLite por Postgres exige editar dezenas de arquivos).
**Exemplo de sinal:** `import database` no topo de cada controller e chamadas diretas a `database.conn.execute(...)` espalhadas pelo código.

### 7. Estado Global Mutável
**Sinais de detecção:** dados de aplicação (lista de usuários, carrinho, contador de IDs) armazenados em variável global de módulo (lista/dict em memória) mutada diretamente por múltiplos handlers, sem camada de persistência real ou controle de concorrência.
**Impacto:** dados perdidos a cada restart, condições de corrida, impossível escalar horizontalmente.
**Exemplo de sinal:** `pedidos = []` no topo do arquivo, com `pedidos.append(...)` dentro de handlers de rota.

### 8. Tratamento de Erros Ausente ou Inconsistente
**Sinais de detecção:** ausência de `try/except`/`try/catch` em operações que podem falhar (parsing de JSON, acesso a banco, chamadas externas); exceções não tratadas vazam stack trace/detalhes internos na resposta HTTP; cada rota trata erro de um jeito diferente (sem handler centralizado).
**Impacto:** vazamento de detalhes internos (informação sensível para um atacante), respostas inconsistentes, crashes não controlados.

---

## MEDIUM

### 9. Queries N+1
**Sinais de detecção:** loop (`for`) que executa uma query de banco a cada iteração, quando uma única query com `JOIN`/`IN`/eager loading resolveria.
**Impacto:** degradação de performance proporcional ao volume de dados.
**Exemplo de sinal:** `for pedido in pedidos: itens = query("SELECT * FROM itens WHERE pedido_id = ?", pedido.id)`.

### 10. Validação de Entrada Ausente nas Rotas
**Sinais de detecção:** handler usa `request.json`/`req.body` diretamente sem checar presença/tipo/formato dos campos obrigatórios antes de usá-los (em query, cálculo, ou resposta).
**Impacto:** erros 500 em vez de 400, dados inconsistentes persistidos, superfície de ataque maior.

### 11. Uso Inadequado de Middlewares
**Sinais de detecção:** middleware global aplicado a todas as rotas quando deveria ser escopado (ex.: CORS liberando `*` em rota de admin), ou lógica que deveria ser middleware (parsing, auth, logging) duplicada manualmente em cada handler.
**Impacto:** inconsistência de comportamento entre rotas, risco de segurança (CORS excessivamente permissivo), duplicação de código.

### 12. APIs / Padrões Deprecated
**Sinais de detecção:** uso de métodos, imports ou padrões marcados como deprecated/removidos na versão da stack detectada. Exemplos comuns a checar:
- **Flask**: `@app.before_first_request` (removido no Flask 2.3+) → usar setup no factory/`with app.app_context()`; `flask.Markup` (removido, migrar para `markupsafe.Markup`); `app.run(debug=True)` deixado ligado em "produção".
- **Python geral**: módulo `cgi`/`imp` (removidos no 3.12/3.13) → `email`/`importlib`; `sqlite3` sem `with` (conexões não fechadas); chamadas de rede (`requests.get`) sem `timeout=`.
- **Express/Node**: `body-parser` como dependência separada em vez de `express.json()`/`express.urlencoded()` nativos (Express 4.16+); `new Buffer()` (deprecated) → `Buffer.from()`; callbacks de `fs` síncronos/antigos em vez de `fs.promises`; `util._extend` → `Object.assign`.
- **Geral**: dependências no manifesto com versão majorformente desatualizada em relação à atual estável, quando isso afeta segurança (ex.: driver de banco sem suporte a prepared statements na versão usada).
**Impacto:** funcionalidade quebra em upgrades futuros, perda de patches de segurança, comportamento não documentado.
**Recomendação:** sempre citar o equivalente moderno ao reportar o finding.

---

## LOW

### 13. Nomenclatura Ruim / Inconsistente
**Sinais de detecção:** nomes de variáveis/funções genéricos (`data`, `x`, `temp`, `foo`), mistura de idiomas (português/inglês) sem padrão, nomes que não refletem o domínio.
**Impacto:** aumenta o tempo de leitura e a chance de erro ao dar manutenção.

### 14. Magic Numbers / Strings Soltos
**Sinais de detecção:** literais numéricos ou de string com significado de negócio embutidos diretamente no código (`if status == 3`, `desconto = valor * 0.15`) sem constante nomeada.
**Impacto:** significado obscuro, difícil de alterar de forma consistente.

### 15. Funções Longas sem Decomposição
**Sinais de detecção:** função/handler com dezenas de linhas fazendo múltiplas coisas sequenciais (parse, validação, cálculo, persistência, resposta) sem estar quebrada em passos nomeados.
**Impacto:** legibilidade e testabilidade reduzidas, mesmo sem violar camadas.

### 16. Duplicação de Código
**Sinais de detecção:** blocos de código quase idênticos repetidos em múltiplos handlers/arquivos (ex.: mesma lógica de conexão a banco copiada em cada rota, mesma validação repetida).
**Impacto:** manutenção duplicada — corrigir um bug exige lembrar de todos os lugares copiados.

---

## Como aplicar este catálogo na Fase 2

1. Percorra o código sistematicamente arquivo por arquivo, checando cada anti-pattern acima.
2. Um mesmo trecho pode gerar mais de um finding (ex.: um arquivo pode ser God Class *e* conter SQL Injection dentro dele — registre ambos separadamente, cada um com sua própria severidade e linha).
3. Nunca reporte um anti-pattern sem apontar arquivo e linha reais — abra o arquivo e confirme o número da linha antes de registrar o finding.
4. Priorize CRITICAL e HIGH no resumo executivo, mas registre também MEDIUM/LOW — o mínimo de findings da auditoria é 5, com pelo menos 1 CRITICAL ou HIGH.
