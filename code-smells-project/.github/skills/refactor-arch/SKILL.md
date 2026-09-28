---
name: refactor-arch
description: "Analyze and refactor legacy API servers to a layered MVC architecture without changing their language, framework, or runtime. Use for architecture audits, code smells, SOLID violations, API modernization, and controller-service-repository refactors."
argument-hint: "[optional project path or scope]"
user-invocable: true
---

# Refactor Legacy APIs to MVC

Audit a legacy API, present an evidence-based plan, and refactor only after the user explicitly approves Phase 3. Preserve the existing language, framework, public API behavior, and runtime dependencies unless the user approves a necessary exception.

## Operating Rules

- Treat the project root as the user-selected directory, the current workspace folder, or the directory explicitly given as an argument. Do not assume the skill's own directory is the target. Resolve and state the root before analysis.
- Keep the work limited to the target API. Do not refactor neighboring projects or unrelated files.
- Never modify application files during Phases 1 or 2. Phase 2 ends by asking whether to proceed; wait for an unambiguous affirmative answer before Phase 3. A prior request to create or invoke this skill is not approval to refactor.
- Keep the original stack. MVC layer names can follow ecosystem conventions, but preserve the dependency direction: HTTP route/view adapter -> controller -> service -> repository. Domain models represent application data and rules; they do not replace these layers.
- Base every finding on inspected code. Cite repository-relative file paths and exact 1-based line numbers. Do not report guesses as findings or promise zero remaining smells without a complete, repeatable check.
- Read the relevant reference before each phase: [project analysis](./references/project-analysis.md), [anti-pattern catalog](./references/anti-pattern-catalog.md), [MVC guidelines](./references/mvc-guidelines.md), [refactoring playbook](./references/refactoring-playbook.md), and [report template](./references/report-template.md).

## Phase 1: Project Analysis

1. Identify the target root and inspect its repository guidance, manifests/lockfiles, entry points, route registration, persistence code, tests, and relevant configuration. Exclude generated output, vendored dependencies, virtual environments, and build artifacts.
2. Use the heuristics in `project-analysis.md` to determine languages, framework and version when verifiable, dependencies, domain, architecture, source-file count, database/tables or collections when discoverable, and the existing endpoint surface.
3. Trace at least one representative request from route through business logic to persistence. Record actual layer boundaries and where responsibilities are mixed.
4. Print the Phase 1 summary using `report-template.md`. Include counts and database details only when verified; label unavailable details as `Not determined` rather than inventing them.

## Phase 2: Architecture Audit and Plan

1. Compare the inspected code with `anti-pattern-catalog.md`. Check security, deprecated APIs, MVC boundaries, SOLID, validation, performance, duplication, and readability. Confirm suspected issues at their source and classify by the highest demonstrated impact.
2. For each finding, include severity, concise title, exact file and line(s), evidence/description, impact, and a concrete recommendation. Use `report-template.md`. Deduplicate symptoms with the same root cause.
3. Review official documentation and authoritative guides for the detected language, framework, database/ORM, and any deprecated API involved. Prefer official documentation for the installed major version. Record links, relevant recommendation, and access date; distinguish verified guidance from general architectural judgment. If network access is unavailable, say so and use only documentation already present in the project or known guidance without claiming it was freshly researched.
4. Present a staged plan ordered by dependencies and risk. Include intended layer/file changes, API and data compatibility strategy, tests to run, and risks. Do not change any project files or create the final report yet.
5. End with the exact approval question: `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` Wait for the user's answer. Continue only after an explicit affirmative response. If declined, stop without modifying the project and provide the audit and plan in the conversation.

## Phase 3: Approved Refactoring

1. Re-read the approved plan and relevant files. Capture a baseline before edits: existing tests, boot command, routes/methods, and available representative responses or documented contracts. Never use destructive database actions or production credentials. If no runnable baseline is available, disclose that and use the strongest safe checks available.
2. Apply the smallest coherent changes that implement the approved plan. Follow `mvc-guidelines.md` and use `refactoring-playbook.md` as patterns, adapting examples to the project's actual stack. Keep routes thin; controllers coordinate; services own use-case/business rules; repositories own persistence; models represent domain/data structures. Preserve endpoint paths, methods, status codes, payloads, and side effects unless the user approved a change.
3. Add or update focused tests for moved behavior and boundary contracts. Preserve existing tests; do not weaken or delete them merely to make the refactor pass. Do not claim an anti-pattern is eliminated unless reinspection verifies it.
4. Validate in increasing cost: syntax/type/lint checks available for the project, focused tests, full test suite, application boot, then endpoint smoke checks against the baseline. Use a safe local/test database. Compare endpoint behavior and report any unavailable or failing validation honestly. Do not state that all endpoints work when only a subset was exercised.
5. Save the complete procedure report as `docs/refactor-report-YYYY-MM-DD.md` in the target root, creating `docs/` if needed. Use the current local date and the template in `report-template.md`. Include Phase 1, findings, official sources reviewed, approved plan, actual changes, validation results, and remaining issues. Avoid secrets and sensitive data in the report.
6. Summarize the resulting structure and validation in the conversation. Clearly separate passed, failed, and not-run checks; mention deviations from the approved plan.

## Completion Criteria

- The stack and current architecture are evidence-backed and reported.
- Findings have severities and exact source locations; deprecated APIs are considered.
- No application edit happened before explicit Phase 3 approval.
- The approved changes preserve the existing technology stack and observable API behavior, or any unavoidable deviation is disclosed.
- Validation claims match commands and endpoint checks actually completed, and the dated report is saved under `docs/`.
