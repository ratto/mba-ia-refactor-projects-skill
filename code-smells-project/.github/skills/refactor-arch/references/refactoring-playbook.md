# Refactoring Playbook

These language-neutral sketches show responsibility movement. Adapt syntax, dependency injection, validation, and framework APIs to the installed versions; preserve current endpoint contracts. Use official stack documentation for concrete APIs.

## 1. Route Contains Business Logic

Before:

```python
@app.post('/orders')
def create_order():
    body = request.json
    total = sum(item['price'] * item['quantity'] for item in body['items'])
    db.execute('INSERT INTO orders(total) VALUES (?)', (total,))
    return {'total': total}, 201
```

After:

```python
@app.post('/orders')
def create_order():
    result = order_controller.create(request.get_json())
    return result.body, result.status

class OrderController:
    def __init__(self, service):
        self.service = service

    def create(self, data):
        return HttpResult(201, self.service.create_order(data))

class OrderService:
    def __init__(self, orders):
        self.orders = orders

    def create_order(self, data):
        total = calculate_total(data['items'])
        return self.orders.create(total, data['items'])
```

## 2. SQL Injection / Unsafe Query

Before:

```python
query = "SELECT * FROM users WHERE email = '" + email + "'"
```

After:

```python
user = repository.find_by_email(email)  # Repository binds email as a query parameter.
```

Use the database driver's parameterized query or safe ORM query API; do not interpolate values.

## 3. Controller Directly Queries the Database

Before:

```javascript
async function show(req, res) {
  const row = await db.query("SELECT * FROM users WHERE id = ?", [
    req.params.id,
  ]);
  res.json(row[0]);
}
```

After:

```javascript
async function show(req, res, next) {
  try {
    res.json(await userController.getById(req.params.id));
  } catch (error) {
    next(error);
  }
}
// Controller calls a service; service calls a user repository; repository owns the query.
```

## 4. Hardcoded Secret

Before:

```javascript
const signingKey = "literal-secret";
```

After:

```javascript
const signingKey = config.require("TOKEN_SIGNING_KEY");
```

Load secrets from the deployment's environment or secret manager, validate presence at startup, and rotate any exposed credential. Never copy the original secret into a report or test.

## 5. Global Mutable Request State

Before:

```javascript
let currentUser;
```

After:

```javascript
function createOrderController({ orderService }) {
  return { create: (userId, input) => orderService.create(userId, input) };
}
// Pass request identity through the framework request/context and explicit use-case arguments.
```

Use framework request-scoped context or explicit parameters; inject stable services at composition time.

## 6. Repeated Validation in Routes

Before:

```javascript
if (!req.body.email || !req.body.email.includes("@"))
  return res.status(400).end();
```

After:

```javascript
const input = validateCreateUser(req.body); // Returns typed data or a boundary validation error.
return userController.create(input);
```

Use the project's existing validation library or a small shared schema. Keep transport validation at the boundary and domain invariants in the use case.

## 7. N+1 Query in a Loop

Before:

```python
for order in orders:
    order['items'] = repository.items_for_order(order['id'])
```

After:

```python
items_by_order = repository.items_for_orders([order['id'] for order in orders])
for order in orders:
    order['items'] = items_by_order.get(order['id'], [])
```

Use a join, eager loading, or a batch query supported by the current ORM/database; verify query count and response equivalence.

## 8. Duplicated Error Mapping

Before:

```python
try:
    result = service.run()
except ValueError:
    return {'error': 'invalid'}, 400
```

The same mapping is copied in several route handlers.

After:

```python
@app.errorhandler(ValidationError)
def validation_error(error):
    return {'error': error.public_message}, 400
```

Centralize transport mapping in the framework's error boundary while preserving existing error payloads and logging internal causes safely.

## 9. Deprecated API

Before:

```javascript
legacyClient.request(url, callback); // Deprecated in the installed client version.
```

After:

```javascript
const response = await supportedClient.fetch(url); // Use the documented replacement for this version.
```

Confirm deprecation and replacement in official version-specific docs; update call sites and tests together. If the replacement changes semantics or package version, include that risk in the Phase 2 plan and obtain approval.

## 10. God Module / Composition Root

Before: one entry file defines routes, SQL, validation, domain workflows, and response formatting.

After: move cohesive responsibilities into route adapters, controllers, services, repositories, and domain models; leave the entry point to configure and wire them. Extract incrementally, preserving imports, startup behavior, middleware order, and endpoint contracts. Do not split a small cohesive module just to satisfy a directory diagram.
