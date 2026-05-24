# v1 / v2 Isolation Risks

## Current state

- good: `tests/unit/asteroid_lab/test_service_import_boundaries.py` forbids old mining solver namespace strings.
- risk: live repo has both `django_apps/shapez_solver` and `django_apps/asteroid_lab`, both using nouns like `SolverRun`, `PatternTemplate`.
- risk: canonical docs used `shapez_asteroid` / `asteroid_mining_layout_v2` as baseline but live app is `asteroid_lab`.

## risk matrix

| File / area | Isolation risk | Root cause | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `tests/unit/asteroid_lab/test_service_import_boundaries.py` | namespace prohibition is substring-level | no graph-level allowed-edge verification | `P2` | High | `test-only` |
| `django_apps/asteroid_lab/models.py` vs `django_apps/shapez_solver/models.py` | duplicate nouns `SolverRun`, `PatternTemplate` | domain vocabulary collision | `P1` | Medium | `isolate` |
| canonical docs vs live tree | v2 docs do not map directly onto current lab shell | missing migration map | `P0` | High | `freeze` |
| `django_apps/asteroid_lab/services/project_service.py` | docstring emphasizes old v1/v2 solver internals unused but live semantic boundary itself is ambiguous | defensive wording replaces structure | `P2` | Medium | `rewrite` |

## What was confirmed

- no multi-file SCC inside `django_apps/asteroid_lab`
- no runtime import of `django_apps.shapez_asteroid`, `asteroid_mining_layout_v1`, `asteroid_mining_layout_v2` from `django_apps/asteroid_lab`

## Remaining risks

1. On canonical solver migration, unclear whether `asteroid_lab` is temporary shell or long-lived app.
2. Model noun collisions make serializer, admin, migration, and docs terminology easy to misread.
3. v2 package assumed by docs does not exist in live repo, so isolation refactor order can invert easily.

## Recommended actions

- declare `asteroid_lab` role clearly in phase 1
  - option A: fixed as inspection/replay sandbox
  - option B: promoted to vanguard package of canonical solver runtime
- either way, build vocabulary collision table with `shapez_solver` first.
