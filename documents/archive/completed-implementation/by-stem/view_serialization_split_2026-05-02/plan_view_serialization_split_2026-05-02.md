# Plan: view_serialization split (2026-05-02)

Related research: [documents/research_view_serialization_split_2026-05-02.md](./research_view_serialization_split_2026-05-02.md)

Original request summary: split graph/preview serialization responsibilities mixed inside `view_serialization.py` while preserving the current API payload contract.

## Implementation approach

1. Extract graph node/edge/preview serialization into a new module.
2. Reduce [view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) to focus on solve result payload, base demand, step, and error payload.
3. Refactor `serialize_solver_result()` to call the new graph serialization helper only.

## Compatibility criteria

- `from django_apps.shapez_solver.view_serialization import serialize_solver_result, error_payload` must keep working.
- Preserve `target`, `target_count`, `base_demands`, `steps`, and `graph` field structure.
- Preserve graph node fields `preview_image_url`, `preview_alt`, `quantity`, `reused_count`.

## Verification

- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m mypy django_apps/shapez_solver/view_serialization.py`
- `python -m ruff check django_apps/shapez_solver/view_serialization.py`
