# Plan: dead code cleanup sequence refactor (2026-05-01)

Related research: [research_dead_code_cleanup_2026-05-01.md](./research_dead_code_cleanup_2026-05-01.md)

Original request summary: clean up dead paths and duplicate solve logic already replaced at runtime, and reduce deletable files in a safe order.

## Implementation approach

1. Extract shared solve pipeline between [django_apps/shapez_solver/services/solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py) and [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) into a common helper.
2. Keep `FactoryThroughputService` as the primary path already used by views and new tests; shrink legacy `SolverService` to one of:
   - Safe option: keep as minimal compatibility wrapper around the shared helper.
   - Deletion option: migrate all repo tests to the new service, then delete the file.
3. Confirm no remaining code/test references to already-deleted [graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py).
4. Absorb duplicate tests into the new service baseline; remove or rename dead contract tests to reflect current contracts accurately.

## Approval points

- Decision needed: delete `solver_service.py` entirely or keep a minimal compatibility shim.
- Default for lower external import risk: safe option (keep shim).
- If user prioritizes “delete the file,” deletion option is possible but tests and import paths change together.

## Compatibility criteria

- Preserve `/api/solver/solve/` response contract.
- Preserve current `target_count`, `base_demands`, and graph target quantity behavior.
- Planner/operation replay verification logic must live in one place only.

## Verification

- `python -m pytest tests/unit/shapez_solver/test_factory_throughput_service.py`
- `python -m pytest tests/unit/shapez_solver/test_solver_service.py`
- `python -m pytest tests/unit/shapez_core/test_shape_code_parser.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m ruff check .`
- `python -m mypy .`
- `python -m black .`
