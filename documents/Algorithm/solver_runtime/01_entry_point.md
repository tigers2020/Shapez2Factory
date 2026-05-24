---
status: ARCHIVED
owner: solver-runtime-pipeline
last_reviewed: 2026-05-22
archived_reason: Solver A→M orchestration removed; HTTP entry returns SOLVER_NOT_AVAILABLE only
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
phase: Entry
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - django_apps/web/views/public_pages.py
---

# Solver Button Entry Point (stub)

## Current behavior (2026-05-22)

The `Run Solver` / `Solver` button returns **HTTP 200** + JSON `ok: false`, `error_code: "SOLVER_NOT_AVAILABLE"`. **500 forbidden.**

```text
POST /asteroid-miner-layout/p/<slug>/run-solver/
```

- URL name: `web:asteroid-miner-layout-project-run-solver`
- View: `asteroid_miner_layout_project_run_solver` ([`public_pages.py`](../../../django_apps/web/views/public_pages.py))
- Service: `run_solver_runtime_for_project` ([`solver_runtime_entry.py`](../../../django_apps/asteroid_lab/services/solver_runtime_entry.py))
- Lab replay frames: reconstruction timeline stored on the project only (`build_lab_replay_frames_for_project`)

## Removed

- `solver_runtime_pipeline` (A→M orchestration)
- `manage.py run_solver`, `scripts/run_solver.ps1`
- Entire `optimization/` package
- Optimization replay persist·12H optimization HUD input

## Reconstruction (ACTIVE)

Map decode·reconstruction·persist·Lab replay remain on paths **independent** of the Solver button. [`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md).

## Forbidden (invariants)

- Using replay artifact as algorithm **input**
- Layout commit·belt/pipe pre-install at entry point

## Tests

- `tests/integration/web/test_asteroid_run_solver.py` — POST → `SOLVER_NOT_AVAILABLE`
- `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

## History

Phase A–M contracts: `phase_*.md` (all `ARCHIVED`). Strip spec: [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md).
