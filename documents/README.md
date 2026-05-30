# `documents/` Index

Project Markdown body text defaults to English. Code, paths, CLI, identifiers,
and URLs remain in their original form.

## Read These First

1. [`README.md`](README.md)
2. [`Algorithm/README.md`](Algorithm/README.md)
3. [`ai/START_HERE.md`](ai/START_HERE.md)
4. [`index/document_inventory.md`](index/document_inventory.md)
5. [`index/document_lifecycle.md`](index/document_lifecycle.md)
6. [`reports/README.md`](reports/README.md)

## Authority Hierarchy

| Scope | Path | Usage Rules |
|---|---|---|
| domain / workflow canonical | [`game_rules/`](game_rules/), accepted ADRs under [`../docs/adr/`](../docs/adr/), root rule files | Current implementation authority |
| canonical routing/index | [`README.md`](README.md), [`Algorithm/README.md`](Algorithm/README.md), [`index/`](index/) | Document location and lifecycle decisions |
| AI workflow/manuals | [`ai/`](ai/) | Work procedures, current plan, checklist, manual routing |
| implementation planning | [`plans/`](plans/), [`ai/plans/`](ai/plans/) | Current approved or pending scope only |
| audit/report/research | [`reports/`](reports/README.md), [`research/`](research/), [`notes/`](notes/), [`debug/`](debug/) | Evidence only, not implementation contracts |
| generated/sample output | [`samples/`](samples/), `var/` | Output evidence only; never algorithm input |

## Current-only Policy

- Archive, obsolete, superseded, and outdated documents are deleted rather than
  retained in the repo.
- Do not recreate deleted holding areas for old documents.
- Remove links to deleted plans, specs, and tests in the same cleanup.
- Promote stable decisions into current `CANON` documents or accepted ADRs.

## Prohibited for Future AI Coding Agents

- Do not read `var/*.ndjson`, replay output, or solver summaries as algorithm
  input.
- Do not use deleted historical content as a current implementation
  contract.
- Do not silently merge historical reports into current specs.
