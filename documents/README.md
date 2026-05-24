# `documents/` Index

Project Markdown body text defaults to English. Code, paths, CLI, identifiers, and URLs remain in their original form.

## Read These First

1. [`README.md`](README.md) — This document. Document authority and reading order.
2. [`Algorithm/README.md`](Algorithm/README.md) — Algorithm document slots (no canonical mining solver content at present).
3. [`ai/START_HERE.md`](ai/START_HERE.md) — AI work session entry point.
4. [`index/document_lifecycle.md`](index/document_lifecycle.md), [`index/document_inventory.md`](index/document_inventory.md) — Document lifecycle and inventory.
5. [`reports/README.md`](reports/README.md) — Report bundle index.

## Authority Hierarchy

| Scope | Path | Usage Rules |
|---|---|---|
| domain / workflow canonical | [`game_rules/`](game_rules/), promoted docs under [`research/`](research/), [`adr/`](adr/), root rule files | When in conflict with implementation or plans, these take precedence. |
| canonical routing/index | [`README.md`](README.md), [`Algorithm/README.md`](Algorithm/README.md), [`index/`](index/) | Used for document location and lifecycle decisions. |
| AI workflow/manuals | [`ai/`](ai/) | Work procedures, current plan, checklist, manual routing. |
| implementation planning | [`plans/`](plans/), [`ai/plans/`](ai/plans/) | For checking approved scope and backlog. Canonical docs take precedence on conflict. |
| audit/report/research | [`reports/`](reports/README.md), [`research/`](research/), [`notes/`](notes/), [`debug/`](debug/)(slot; may have no files), [`archive/refactor_audit_pre_mining_solver_removal_2026-05/`](archive/refactor_audit_pre_mining_solver_removal_2026-05/README.md) | Observational evidence and analysis. Historical reports are not current truth. Audit bundles may cite removed canonical docs — read archive only. |
| historical/obsolete | [`archive/`](archive/), [`refactory/`](refactory/) | For historical reference. Do not use directly for current implementation decisions. |
| generated/sample output | [`samples/`](samples/), `var/` | Output evidence only. Do not use as algorithm input. |

## Using Implementation Plans and Reports

- `plans/` and `ai/plans/` are pre/during-implementation plans. Documents that are complete or obsolete should be reviewed as archive candidates.
- `reports/` and `research/` are evidence and decision records. To promote to canonical, follow ADR · game_rules · research promotion procedures.
- `documents/reports/README.md` is the current routing index for report bundles.

## Prohibited for Future AI Coding Agents

- Do not read `var/*.ndjson`, replay output, or solver_summary and use them as **recipe solver** algorithm input.
- Past mining layout · asteroid-related archive/plan body text is for **git history** only. Do not use as current app implementation contract.
- Do not silently merge historical reports into current spec. On conflict, mark as drift/obsolete.
