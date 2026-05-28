---
status: RETIRED_ARCHIVE
do_not_execute: true
superseded_by: docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md
---

# Strip Solver — Keep Reconstruction Complete — Implementation Plan

> **Status:** Executed 2026-05-22  
> **Spec:** [`2026-05-22-strip-solver-keep-recon-complete-design.md`](../specs/2026-05-22-strip-solver-keep-recon-complete-design.md)

**Goal:** Remove post-reconstruction solver/optimization code; keep Lab reconstruction through `reconstruction.complete`.

**Architecture:** Extraction-first — `acceptance_topology`, `grid_contract`, `contracts/game_data_snapshot`, `genetic_sample/*` — then delete `optimization/` and solver pipeline modules; stub `solver_runtime_entry`.

---

## Gate verification (post-surgery)

| Gate | Result |
|------|--------|
| GATE-1 | `reconstruction/` has zero `optimization` imports |
| GATE-2 | `django_apps/asteroid_lab/optimization/` removed |
| GATE-3 | `test_reconstruction_fixture_contract`, persist/replay/timeline tests pass |
| GATE-4 | `test_asteroid_run_solver` — HTTP 200 + `SOLVER_NOT_AVAILABLE` |
| GATE-5 | `solver_runtime_pipeline` deleted; entry stub-only |
| GATE-6 | shadow/rd_gate scripts removed |
| GATE-7 | `solver_runtime/README.md` → ARCHIVED |

## Commands

```bash
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py
python -m pytest tests/integration/web/test_asteroid_run_solver.py
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/contracts django_apps/asteroid_lab/genetic_sample
```
