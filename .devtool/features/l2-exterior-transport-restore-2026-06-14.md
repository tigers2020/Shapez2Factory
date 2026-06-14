---
status: verify
modified: 2026-06-14
---

# L2 exterior transport restore

## Scope

User request: restore Layer 2 exterior transport algorithm from git (pre–algorithm-reset `597cdaf2`). Core authority in `src/`; Django shim only.

## Acceptance

- [x] `layer_02_exterior_transport/` core modules restored (`plan`, `placement`, `slots`, …)
- [x] Django `run.py` shim reexports core (no algorithm modules in django_apps)
- [x] L2 unit tests restored / paths updated to core package
- [x] L2 skeleton contract test removed from `test_layer_skeleton_reset.py`
- [x] `pytest` targeted L2 suite green

## Progress

- 2026-06-14 — restore from `597cdaf2` via `git checkout` on core + tests + django shim.
- 2026-06-14 — verify — `pytest tests/unit/asteroid_lab/layers/test_layer_02_*` 52 passed; run_solver produces `solver_runtime_wires` with L2 plan; gate `OVERALL_OK=true`.
