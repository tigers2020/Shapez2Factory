# AI Context Start Here

This file is the entry point that new AI sessions, subagents, and Cursor work read first when establishing document context.

## Reading order

1. [`../../AGENTS.md`](../../AGENTS.md)
2. [`../index/document_lifecycle.md`](../index/document_lifecycle.md)
3. [`../index/document_inventory.md`](../index/document_inventory.md)
3.5. [`contamination_policy.md`](contamination_policy.md) — forbidden patterns (on conflict, inventory topic row wins)
4. Task-type-specific [`manuals/`](manuals/) documents
5. The current task's [`current_plan.md`](current_plan.md) and [`checklist.md`](checklist.md)
6. Required `CANON` documents

## Authority rules

- Only `CANON` is the current system contract.
- `ACTIVE` is an in-progress plan; it is not authoritative until complete.
- `RESEARCH` is evidence and experiments; it is not an implementation contract.
- `REPORT` is observation and log analysis; it is not design authority.
- `ARCHIVED` and `SUPERSEDED` are for historical reference only. Do not use them for implementation decisions.

## Asteroid Lab / RTTP work

1. [`current_plan.md`](current_plan.md) — active runtime paths and queue
2. [`../index/document_inventory.md`](../index/document_inventory.md) — **§ Asteroid Lab authority by topic**
3. [`contamination_policy.md`](contamination_policy.md) — forbidden patterns and PR playbook
4. Topic authority from inventory row (`docs/superpowers/specs/` or `documents/Algorithm/asteroid_lab_*.md`)
5. Code: `django_apps/asteroid_lab/` + `tests/unit/asteroid_lab/`

The following contracts take precedence over older plans/reports (when the topic row is more specific, **row wins**):

- Placement ≠ Commit; route probe at candidate creation
- validation read-only; replay/artifacts output-only
- single `RouteDomainSnapshotBuilder` owner

**Forbidden:** Do not use `documents/plans/asteroid_lab_optimization/` as implementation authority.

**Forbidden:** Do not use `django_apps.shapez_asteroid`, `tests/unit/shapez_asteroid` as current work paths.

## Forbidden

- Do not use content from `documents/archive/` as current implementation authority.
- Do not promote `documents/debug/` or progress reports to spec status.
- When you find competing specs, do not implement immediately; mark as `SUPERSEDED` candidates or leave an inventory cleanup item.
- Do not add experiments, TODOs, or log analysis to grow canon. Canon holds only stable invariants and contracts.
