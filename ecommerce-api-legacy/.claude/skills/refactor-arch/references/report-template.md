# Templates de Relatório

Use estes formatos literalmente (mesmos separadores, mesmos títulos de seção) para que a saída seja consistente entre projetos e stacks.

## Fase 1 — PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem detectada>
Framework:      <framework + versão, ou "none/framework-less">
Dependencies:  <lista curta separada por vírgula das dependências relevantes>
Domain:        <domínio de negócio em 1 frase>
Architecture:  <classificação — Monolítica / Parcialmente organizada / MVC bem aplicado — + 1 frase de justificativa>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/coleções, ou "none (in-memory state)">
================================
```

## Fase 2 — ARCHITECTURE AUDIT REPORT

```
================================
PHASE 2: ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<N> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Nome do anti-pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que está errado, objetivamente>
Impact: <consequência concreta>
Recommendation: <correção sugerida, alinhada ao playbook>

<... um bloco por finding, ordenado CRITICAL -> HIGH -> MEDIUM -> LOW ...>

## Proposed MVC Structure
<árvore de diretórios alvo proposta para este projeto especificamente>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Após imprimir isso, **pare e aguarde a resposta do usuário** antes de continuar.

## Fase 3 — REFACTORING COMPLETE

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios final, real>

## Findings Resolved
<lista curta: quantos CRITICAL/HIGH/MEDIUM/LOW foram corrigidos, e quais ficaram pendentes com justificativa, se houver>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

Se algum item da validação falhar, não marque com ✓ — reporte com ✗ e a causa, e corrija antes de considerar a fase concluída.

## Relatório final em `docs/refactor-report-<YYYY-MM-DD>.md`

Deve consolidar em Markdown, nesta ordem:

1. Título e data.
2. Cópia do resumo da Fase 1.
3. Cópia completa do relatório da Fase 2 (todos os findings).
4. Confirmação do humano recebida (texto literal da aprovação).
5. Cópia do resumo da Fase 3 (estrutura nova + validação).
6. Seção "Decisões e Trade-offs" com qualquer desvio do plano original e o motivo.
