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

## Asteroid Lab (reconstruction slice — post P0 decontamination)

1. [`current_plan.md`](current_plan.md) — runtime (`SOLVER_NOT_AVAILABLE`) and standing gates
2. [`../index/document_inventory.md`](../index/document_inventory.md) — **§ Asteroid Lab authority by topic**
3. [`contamination_policy.md`](contamination_policy.md) — forbidden patterns and PR playbook
4. Normative specs: [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md), [`2026-05-26-reconstruction-complete-map-dto-design.md`](../../docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md)
5. Code: `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`, `services/solver_runtime_entry.py` + `tests/unit/asteroid_lab/` (reconstruction narrow gates)

**Active contracts (reconstruction):**

- `ReconstructionCompleteMap` is terrain/capacity SoT at pipeline boundaries
- Replay/artifacts are output-only (not algorithm inputs)
- `run_solver` is fail-closed stub only — **no RTTP pipeline**

**Forbidden:** Do not implement from RTTP queue rows, `documents/archive/asteroid_lab_rttp_retired_2026-05/` (except FROZEN MEG contract read-only), or retired `documents/Algorithm/asteroid_lab_01`–`08` / `solver_runtime/` archives.

**Forbidden:** Do not use `documents/plans/asteroid_lab_optimization/` as implementation authority.

**Forbidden:** Do not use `django_apps.shapez_asteroid`, `django_apps/asteroid_lab/optimization/`, `tests/unit/shapez_asteroid` as current work paths.

## Forbidden

- Do not use content from `documents/archive/` as current implementation authority.
- Do not promote `documents/debug/` or progress reports to spec status.
- When you find competing specs, do not implement immediately; mark as `SUPERSEDED` candidates or leave an inventory cleanup item.
- Do not add experiments, TODOs, or log analysis to grow canon. Canon holds only stable invariants and contracts.
