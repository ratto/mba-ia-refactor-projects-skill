# Report Templates

Use repository-relative paths and 1-based line numbers. Replace all placeholders, omit unsupported claims, redact secrets, and keep the audit report distinct from the Phase 1 summary.

## Phase 1: Project Analysis

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       <project directory/name>
Language:      <verified language(s)>
Framework:     <name and verified version, or Not determined>
Dependencies:  <relevant used dependencies>
Domain:        <evidence-based short description>
Architecture:  <current architecture and actual layer boundaries>
Source files:  <count> files analyzed (<inclusion rule>)
Database:      <engine and known tables/collections, or Not determined>
Endpoints:     <count/inventory or Not determined>
================================
```

## Phase 2: Architecture Audit Report

```text
================================
PHASE 2: ARCHITECTURE AUDIT REPORT
================================
Project: <name>
Stack:   <language + framework/version>
Files:   <count> analyzed | <approximate LOC only if measured>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <specific pattern>
File: <relative/path.ext>:<line or start-end>
Description: <observed behavior and evidence>
Impact: <demonstrable consequence>
Recommendation: <small actionable correction>

## Official Guidance Reviewed
- <official document title and URL> — <recommendation relevant to this plan>; accessed <YYYY-MM-DD>

## Proposed Plan
1. <ordered change, files/layers, compatibility note>

================================
Total: <n> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Print actual findings, not the placeholders. If no finding is verified, report zero with the checks performed. Include deprecated API evidence and replacement where applicable.

## Dated Final Report

Save as `docs/refactor-report-YYYY-MM-DD.md` in the target project root. Include:

1. Run date, project root, initial stack, and Phase 1 summary.
2. Full Phase 2 findings and counts, including exact locations.
3. Official sources reviewed (title, URL, access date) and the approved plan.
4. Explicit user approval to proceed, or record that Phase 3 was declined and no files were changed. If declined, the interactive workflow does not create this Phase 3 report unless the user separately asks to save the audit.
5. Actual refactoring performed: old/new structure, changed responsibilities, compatibility decisions, and deviations from plan.
6. Validation table with command/check, result, and scope. Include boot and endpoint smoke tests, baseline comparison, tests not run, and known failures.
7. Remaining findings/risks and any behavior changes.

Never write `Zero anti-patterns remaining` unless a defined catalog-wide re-audit was completed; prefer an exact count and scope of residual findings.
