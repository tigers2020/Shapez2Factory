# Plan: shapez_solver views split (2026-05-01)

Related research: [documents/research_shapez_solver_views_split_2026-05-01.md](./research_shapez_solver_views_split_2026-05-01.md)

Original request summary: split request parsing and response serialization responsibilities in [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) while preserving endpoints and JSON payload contracts.

## Implementation approach

1. Extract request parsing (`code`, `target_count`, `max_depth`, JSON body interpretation) into `view_request_parsing.py`.
2. Extract success/failure payload and graph/preview serialization into `view_serialization.py`.
3. Refactor [views.py](../../../../../django_apps/shapez_solver/views.py) into a thin controller focused on service calls and exception mapping.

## Compatibility criteria

- Preserve `/api/solver/solve/` route and `solve_shape` function.
- Do not change response structure for `INVALID_REQUEST`, `EMPTY_SHAPE_CODE`, `SHAPE_CODE_PARSE_ERROR`, `INVALID_TARGET_COUNT`, `UNSUPPORTED_TARGET`, `SOLVER_VALIDATION_ERROR`.
- Preserve graph node/edge, preview scene, and operation icon serialization field names.

## Verification

- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
