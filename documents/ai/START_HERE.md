# AI Context Start Here

Entry point for AI sessions. Workflow: **Spec-first → Contract/Test → Small PR → Gate → Review**.

## Reading order

1. [`../../AGENTS.md`](../../AGENTS.md)
2. [`../../structure.md`](../../structure.md)
3. Task **CANON spec** or [`templates/contract-brief.md`](templates/contract-brief.md)
4. Active **PR plan** when referenced ([`templates/pr-plan.md`](templates/pr-plan.md) · `docs/superpowers/plans/…`)
5. Task-type manual ([`manuals/`](manuals/))
6. [`../index/document_inventory.md`](../index/document_inventory.md) + [`../index/document_lifecycle.md`](../index/document_lifecycle.md)
7. Relevant source + tests only

## Authority rules

| Status | Role |
|---|---|
| **CANON** spec / ADR | Design authority for that contract |
| **ACTIVE** plan | Execution tracker — not final authority |
| **RESEARCH / REPORT** | Evidence only |
| **Superseded / deleted** | Not implementation context |

Templates: [`templates/`](templates/) · Workflow stages: [`../../protocols/README.md`](../../protocols/README.md)

## Asteroid Lab

Current authority:

1. Active CANON spec under `docs/superpowers/specs/` (see [`current_plan.md`](current_plan.md))
2. [`../index/document_inventory.md`](../index/document_inventory.md)
3. Code: `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`, `contracts/`, `services/solver_runtime_entry.py`, `src/shapez2_factory/`
4. [`asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc) + current tests

Active contracts (summary):

- `ReconstructionCompleteMap` = terrain/capacity SoT at pipeline boundaries
- Replay and artifacts = output-only
- `run_solver` = fail-closed unless current CANON spec says otherwise

Forbidden:

- Revive deleted algorithms from old plans or removed tests
- Use superseded Layer 3/4 greedy docs as authority after reset spec
- Grow canon via experiments, TODOs, or log mining

## Agent task minimum

Every implementation task should state:

```text
Position · Mission · Authority (may/must not) · Acceptance · Stop conditions
```

See [`AGENTS.md` § Task prompt contract](../../AGENTS.md).
