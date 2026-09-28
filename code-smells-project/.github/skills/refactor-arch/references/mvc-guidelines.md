# MVC and Layering Guidelines

The target is a simple, testable API architecture that preserves the existing stack. Follow the dependency flow:

`HTTP routes/views -> controllers -> services -> repositories -> database/external persistence`

Domain models/entities describe domain data and invariants and may be used by services/repositories. Dependencies should point inward; domain rules must not depend on HTTP or a specific database driver.

## Responsibilities

- **Views / routes / HTTP adapters:** Declare paths, methods, middleware, and transport concerns. Parse transport input, invoke a controller, and map its result to status/headers/body. Keep handlers thin; no business rules or direct queries.
- **Controllers / handlers:** Coordinate a request with the relevant service, translate validated request data into a use-case call, and translate the outcome to the HTTP contract. Do not implement business policy or issue persistence queries.
- **Services / use cases:** Own application workflows, business decisions, authorization rules requiring domain context, and transaction coordination. Depend on repository abstractions or appropriately narrow persistence APIs. Return domain/application results, not framework response objects.
- **Repositories / data access:** Encapsulate queries and persistence mapping. Do not decide HTTP status or implement use-case policy. Use parameterized queries or safe ORM APIs.
- **Models / entities:** Represent domain concepts, relationships, and local invariants. Do not become a dumping ground for routing, unrelated services, or response formatting.
- **Composition root/configuration:** Construct and wire dependencies, load configuration from environment/secret stores, register routes and middleware. Avoid import-time side effects and mutable request state.
- **Middleware:** Handle cross-cutting transport concerns such as authentication, request IDs, and error boundaries. Use framework ordering correctly; keep domain-specific decisions in the relevant use case.

## SOLID and KISS in Practice

- Apply single responsibility at meaningful change boundaries, not one file/class per trivial function.
- Depend on stable abstractions where they enable substitution, testing, or a real boundary. Avoid interface layers with only ceremonial value.
- Inject dependencies through constructors/factories or the framework's established mechanism; do not add a global service locator.
- Validate untrusted input at the HTTP boundary and enforce important domain invariants in the domain/use-case layer.
- Centralize error translation without swallowing causes; keep API error shape compatible.
- Keep transactions around use cases that require atomicity. Avoid leaking ORM sessions across unrelated layers.
- Match the project's conventions and framework idioms. Names may differ, but responsibilities and dependency direction must remain.
- Preserve endpoint paths, methods, status codes, schemas, authentication, and side effects. Treat any behavior change as a separate approved change.

## Choosing Scope

Refactor by vertical slice where practical: one endpoint through route/controller/service/repository with tests, then repeat. Do not create empty layers or move code mechanically if responsibilities remain coupled. For a small app, a few cohesive modules can satisfy these boundaries; propose larger restructuring only when evidence justifies it.
