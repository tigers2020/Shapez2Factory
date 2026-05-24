# Plan: planner_service split (2026-05-01)

Related research: [documents/research_planner_service_split_2026-05-01.md](./research_planner_service_split_2026-05-01.md)

Original request summary: split internal responsibilities of [django_apps/shapez_solver/services/planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py) while preserving public types and import paths.

## Implementation approach

1. Extract shared operation recipe assembly and shape helpers into `planner_support.py`.
2. Extract source / rotation / stack / paint / half assembly / quadrant assembly / cut search rules into `planner_rules.py`.
3. Leave [planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py) with errors/DTOs, `PlannerService.plan()`, and `PlannerService.solve_shape()` orchestration only.
4. Add planner-specific unit tests to catch graph builder breakage and validate the split path.

## Compatibility criteria

- `from django_apps.shapez_solver.services.planner_service import PlannerService, PlannerRequest, PlannerResult, UnsupportedTargetError` must keep working.
- Preserve solver rule priority and cost comparison (`cost.as_sort_key()`).
- Do not change unsupported material, cycle detection, memoization, or source/paint/stack/rotation/cut rule behavior.

## Verification

- Add and run planner-specific test file.
- Run existing planner-related tests when possible.
- Report full web smoke failures separately from current `graph_builder` import issues.
