# dead code cleanup research (2026-05-01)

- User request is a sequence refactor to delete dead files and duplicate code.
- Current worktree is already dirty from several split refactors in progress. Notably [django_apps/shapez_solver/services/graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py) was deleted and replacement [recipe_graph_builder.py](../../../../../django_apps/shapez_solver/services/recipe_graph_builder.py) was added.
- Runtime path shows [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) already uses [FactoryThroughputService](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) and no longer calls [SolverService](../../../../../django_apps/shapez_solver/services/solver_service.py).
- However [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py) and [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) share nearly duplicate core solve pipelines: `PlannerService.solve_shape()`, `OperationEngine.evaluate()` validation, `RecipeGraphBuilder.build()`, `SolveStep` assembly.
- `SolverService` references remain only in tests. Confirmed paths: [tests/unit/shapez_solver/test_solver_service.py](../../../../../tests/unit/shapez_solver/test_solver_service.py) and [tests/unit/shapez_core/test_shape_code_parser.py](../../../../../tests/unit/shapez_core/test_shape_code_parser.py).
- Therefore the largest duplicate removal candidate is `solver_service.py` itself, or at minimum extracting its internal solve logic into a shared helper.
- Frontend [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) and [shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) became thin entrypoints to submodule directories but may still load from templates; risky to treat as dead files. Safer to view as public entrypoints, not deletion candidates.
- [django_apps/shapez_solver/services/graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py) deletion already progressed; remaining work is reference cleanup and test/compatibility layer reduction.
- Safe deletion order: confirm complete `graph_builder` reference removal → remove or shim `solver_service` callers → update tests to new service baseline → decide dead file deletion last.
- Two risks:
  1. `solver_service.py` may have private dependencies imported outside the repo.
  2. `test_solver_service.py` is both simple regression test and documents prior public contract; deletion requires test meaning redesign.
