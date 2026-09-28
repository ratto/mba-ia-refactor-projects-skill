# Project Analysis Heuristics

Use evidence from manifests, lockfiles, imports, entry points, configuration, route registration, database initialization, and tests. A dependency listed in a manifest is not proof that it is actively used. Report uncertainty explicitly.

## Detect the Stack

- **Python:** `pyproject.toml`, `requirements*.txt`, `Pipfile`, imports, WSGI/ASGI entry points. Identify Flask (`Flask`/`flask`), Django (`django`), FastAPI (`FastAPI`), or the framework established by source and dependencies. State Python/framework versions only when project metadata or runtime output supports them.
- **JavaScript/TypeScript:** `package.json` and lockfile, source extensions, imports, scripts, and entry point. Check Express, Fastify, NestJS, Koa, or other actual framework usage. Distinguish JavaScript from TypeScript and declared dependencies from imported ones.
- **Java/JVM:** Maven/Gradle build files, source layout, runtime/toolchain declarations, and imports. Check Spring MVC/Boot, Jakarta REST, or the framework in use.
- **.NET:** project/solution files, target framework, package references, `Program.cs`, and endpoint/controller registration. Check ASP.NET Core MVC/minimal APIs.
- For other stacks, use their canonical manifest and source conventions; do not force them into a familiar framework label.

## Map the Application

Inspect likely application code while excluding `.git`, dependency directories (`node_modules`, virtual environments), caches, generated/build output, and database binaries. Count analyzed source files and state the inclusion rule. Find:

1. Composition root and configuration loading.
2. Route/controller/handler registration and externally observable HTTP methods and paths.
3. Business/use-case logic and validation.
4. Data models/entities and persistence boundaries.
5. Middleware, authentication/authorization, error handling, and external integrations.
6. Tests and available run/test commands.

Trace representative read and write requests end-to-end. Record where the responsibilities reside, dependencies between layers, and shared mutable state. Use call sites, not filenames alone, to establish architecture.

## Database and Domain

Identify database engine and access library from configuration/code; never print credential values. List table/collection names only when visible in schema, migrations, ORM declarations, or safe local metadata. Describe the domain from routes, models, and use cases; keep it concise and do not infer undocumented business rules.

## Phase 1 Summary Fields

Report language(s), framework/version, principal dependencies, domain, current architecture, source files analyzed, database/tables or collections if known, and endpoint count or inventory if useful. Mark unknown fields `Not determined`. The summary is a verified snapshot, not a desired-state architecture.
