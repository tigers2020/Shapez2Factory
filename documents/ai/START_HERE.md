# AI Context Start Here

This is the entry point for AI sessions and subagents when selecting current
project context.

## Reading Order

1. [`../../AGENTS.md`](../../AGENTS.md)
2. [`../index/document_inventory.md`](../index/document_inventory.md)
3. [`../index/document_lifecycle.md`](../index/document_lifecycle.md)
4. Task-type-specific [`manuals/`](manuals/) documents
5. The task's [`current_plan.md`](current_plan.md) and [`checklist.md`](checklist.md)
6. Required current `CANON` documents

## Authority Rules

- Only current `CANON` documents are system contracts.
- `ACTIVE` documents are in-progress plans, not final authority.
- `RESEARCH` and `REPORT` documents are evidence, not design authority.
- Deleted plans, deleted specs, and deleted archive documents are not project
  context for implementation decisions.

## Asteroid Lab

Current authority:

1. [`current_plan.md`](current_plan.md)
2. [`../index/document_inventory.md`](../index/document_inventory.md)
3. Code under `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`,
   `contracts/`, and `services/solver_runtime_entry.py`
4. Task-specific manuals and current tests

Active contracts:

- `ReconstructionCompleteMap` is the terrain/capacity source of truth at pipeline
  boundaries.
- Replay and artifacts are output-only.
- `run_solver` is fail-closed unless a current accepted contract says otherwise.

Forbidden:

- Do not revive deleted solver algorithms from old plans, archive history, or
  removed tests.
- Do not use deleted document paths as implementation context.
- Do not add experiments, TODOs, or log analysis to grow canon.
