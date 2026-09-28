# Playbook de Refatoração

Padrões concretos de transformação, um por anti-pattern do catálogo. Exemplos em Python/Flask e Node/Express — aplique o equivalente idiomático da stack real detectada na Fase 1, mantendo a stack original.

---

## 1. Extrair credenciais hardcoded para configuração

**Antes (Python):**
```python
app.config['SECRET_KEY'] = 'minha-chave-super-secreta-123'
```
**Depois:**
```python
# config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]  # falha explicitamente se ausente

# app.py
app.config['SECRET_KEY'] = settings.SECRET_KEY
```
**Antes (Node):**
```js
const JWT_SECRET = "senha123";
```
**Depois:**
```js
// config/index.js
module.exports = {
  jwtSecret: process.env.JWT_SECRET,
};
```
Adicione `.env.example` com as chaves (sem valores reais) e confirme que `.env` está no `.gitignore`.

---

## 2. Parametrizar queries (eliminar SQL Injection)

**Antes:**
```python
query = f"SELECT * FROM usuarios WHERE id = {user_id}"
cursor.execute(query)
```
**Depois:**
```python
cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
```
**Antes (Node):**
```js
db.query(`SELECT * FROM users WHERE email = '${email}'`);
```
**Depois:**
```js
db.query("SELECT * FROM users WHERE email = ?", [email]);
```

---

## 3. Separar God Class/God File em camadas

**Antes:** um único `models.py`/`app.js` com rotas + SQL + validação + regra de negócio de produtos, pedidos e usuários misturados.

**Depois:** dividir por domínio e por responsabilidade — um Model/Repository, um Service, um Controller e um arquivo de Routes por entidade (ver árvore completa em `architecture-guidelines.md`). Mova cada responsabilidade para seu lugar sem reescrever a lógica de negócio, apenas realocando e ajustando imports.

```python
# models/produto_model.py — só acesso a dados
class ProdutoRepository:
    def find_all(self): ...
    def find_by_id(self, id): ...

# services/produto_service.py — só regra de negócio
class ProdutoService:
    def __init__(self, repository: ProdutoRepository):
        self.repository = repository
    def listar_disponiveis(self):
        return [p for p in self.repository.find_all() if p.estoque > 0]

# controllers/produto_controller.py — só orquestração HTTP
def listar_produtos():
    produtos = produto_service.listar_disponiveis()
    return jsonify([p.to_dict() for p in produtos]), 200

# routes/produto_routes.py — só mapeamento HTTP
produto_bp.route('/produtos', methods=['GET'])(produto_controller.listar_produtos)
```

---

## 4. Adicionar autenticação/autorização em rotas sensíveis

**Antes:**
```python
@app.route('/usuarios/<id>', methods=['DELETE'])
def deletar_usuario(id):
    db.execute("DELETE FROM usuarios WHERE id = ?", (id,))
```
**Depois:**
```python
@app.route('/usuarios/<id>', methods=['DELETE'])
@requer_autenticacao
@requer_permissao('admin')
def deletar_usuario(id):
    usuario_controller.deletar(id)
```
Implemente `requer_autenticacao`/`requer_permissao` como middleware/decorator reutilizável em `middlewares/auth.py`, aplicado a todas as rotas sensíveis — não replique a checagem manualmente em cada handler.

---

## 5. Mover lógica de negócio do Controller para o Service

**Antes:**
```python
@app.route('/pedidos', methods=['POST'])
def criar_pedido():
    data = request.json
    total = sum(item['preco'] * item['qtd'] for item in data['itens'])
    if total > 500:
        total *= 0.9  # desconto
    pedido_id = db.execute("INSERT INTO pedidos ...")
    return jsonify({"id": pedido_id, "total": total})
```
**Depois:**
```python
# controllers/pedido_controller.py
def criar_pedido():
    dados = request.json
    pedido = pedido_service.criar(dados)
    return jsonify(pedido.to_dict()), 201

# services/pedido_service.py
DESCONTO_ACIMA_DE = 500
PERCENTUAL_DESCONTO = 0.9

class PedidoService:
    def criar(self, dados):
        total = self._calcular_total(dados['itens'])
        return self.repository.criar(dados, total)

    def _calcular_total(self, itens):
        total = sum(item['preco'] * item['qtd'] for item in itens)
        if total > DESCONTO_ACIMA_DE:
            total *= PERCENTUAL_DESCONTO
        return total
```

---

## 6. Introduzir injeção de dependência (reduzir acoplamento)

**Antes:**
```python
# controllers/produto_controller.py
import database  # importa conexão global diretamente

def listar():
    return database.conn.execute("SELECT * FROM produtos").fetchall()
```
**Depois:**
```python
# app.py (composition root) — monta as dependências uma vez
produto_repository = ProdutoRepository(db_connection)
produto_service = ProdutoService(produto_repository)
produto_controller = ProdutoController(produto_service)
```
Cada camada recebe suas dependências via construtor/parâmetro, em vez de importar globais — isso torna cada camada testável isoladamente com um mock/stub.

---

## 7. Eliminar estado global mutável

**Antes:**
```python
pedidos = []  # "banco de dados" em memória, global

@app.route('/pedidos', methods=['POST'])
def criar_pedido():
    pedidos.append(request.json)
```
**Depois:** mover para um Repository real, apoiado em banco de dados persistente (o mesmo que já existir no projeto, ou SQLite/arquivo se não houver banco real — sem introduzir uma stack de banco nova). Se o escopo não permite banco real, ao menos isole o estado em uma classe/módulo Repository com métodos controlados (`add`, `list`, `find_by_id`) em vez de lista/dict global mutada em qualquer lugar do código.

---

## 8. Centralizar tratamento de erros

**Antes:** cada rota com seu próprio `try/except` inconsistente, ou nenhum tratamento, deixando o stack trace vazar na resposta.

**Depois (Flask):**
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle_error(err):
    status = getattr(err, 'status_code', 500)
    return jsonify({"error": str(err)}), status
```
**Depois (Express):**
```js
// middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  const status = err.statusCode || 500;
  res.status(status).json({ error: err.message });
};

// app.js — registrado por último
app.use(errorHandler);
```

---

## 9. Corrigir queries N+1

**Antes:**
```python
for pedido in pedidos:
    itens = db.execute("SELECT * FROM itens WHERE pedido_id = ?", (pedido.id,))
```
**Depois:**
```python
pedido_ids = [p.id for p in pedidos]
itens = db.execute(
    f"SELECT * FROM itens WHERE pedido_id IN ({','.join('?' * len(pedido_ids))})",
    pedido_ids,
)
itens_por_pedido = group_by(itens, key='pedido_id')
```
(Ou usar `JOIN`/eager loading do ORM, se disponível — `joinedload`, `populate`, `include`, conforme a stack.)

---

## 10. Adicionar validação de entrada nas rotas

**Antes:**
```python
@app.route('/produtos', methods=['POST'])
def criar_produto():
    data = request.json
    db.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (data['nome'], data['preco']))
```
**Depois:**
```python
def criar_produto():
    dados = request.json
    erros = validar_produto(dados)  # checa campos obrigatórios/tipos
    if erros:
        return jsonify({"errors": erros}), 400
    produto_controller.criar(dados)
```
Use uma lib de schema idiomática da stack quando o projeto já tiver uma dependência disponível para isso (`pydantic`/`marshmallow` em Python, `zod`/`joi` em Node); caso contrário, uma função de validação simples é suficiente (KISS — não adicione uma dependência nova só para isso, a menos que o projeto já tenda nessa direção).

---

## 11. Substituir APIs deprecated pelo equivalente moderno

**Antes (Flask):**
```python
@app.before_first_request
def setup():
    init_db()
```
**Depois:**
```python
with app.app_context():
    init_db()
```
**Antes (Node):**
```js
const bodyParser = require('body-parser');
app.use(bodyParser.json());
```
**Depois:**
```js
app.use(express.json());
```
Sempre cite, no relatório, qual API estava deprecated e qual o equivalente aplicado.

---

## 12. Extrair magic numbers e melhorar nomenclatura

**Antes:**
```python
if status == 3:
    ...
desconto = valor * 0.15
```
**Depois:**
```python
STATUS_CANCELADO = 3
PERCENTUAL_DESCONTO_PADRAO = 0.15

if status == STATUS_CANCELADO:
    ...
desconto = valor * PERCENTUAL_DESCONTO_PADRAO
```
Renomeie identificadores genéricos (`data`, `x`, `temp`) para nomes que reflitam o domínio (`pedido_data`, `produto_id`, `total_calculado`).

---

## Ordem recomendada de aplicação na Fase 3

1. Segurança primeiro: (1) segredos, (2) SQL Injection, (4) auth ausente.
2. Estrutura: (3) separar God Class nas camadas, (6) DI, (7) estado global.
3. Comportamento: (5) mover regra de negócio, (8) erros centralizados, (11) deprecated.
4. Qualidade: (9) N+1, (10) validação, (12) nomenclatura/magic numbers.

Isso garante que, se o tempo/escopo for limitado, os findings mais graves já estarão corrigidos antes dos de baixo impacto.
