# planner_rules.py research

Date: 2026-05-02

## Targets

- `django_apps/shapez_solver/services/planner_rules.py`
- `django_apps/shapez_solver/services/planner_service.py`
- `tests/unit/shapez_solver/test_planner_service_refactor.py`

## Current observations

- `planner_rules.py` works well as rule function collection but operation recipe assembly repeats across rules.
- Repeat patterns are mostly:
  - single-input operation recipe creation
  - binary-input operation recipe creation
- `try_rotation()` and `try_cut_from_source()` iterate derivative candidates with duplicated operation assembly.
- `planner_service.py` is already orchestration-centric; next maintenance cost is larger on `planner_rules.py` side.

## Contracts to preserve

- Keep external public function names.
- Do not break `planner_service.py` import paths.
- Preserve per-rule result shape, cost comparison, and `UnsupportedTargetError` flow.

## Refactoring points

- Internal helper injecting catalog default label/description greatly reduces duplication.
- Separate single/binary operation assembly helpers let each rule state intent directly.
- cut-from-source BFS bundles into “make next derivative candidate” helper for shorter body.

## Cautions

- Goal is readability, not performance; do not change rule order or selection criteria.
- Preserve operation type, selected output index, description override to avoid breaking passing planner tests.
