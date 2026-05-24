# planner_service split research (2026-05-01)

- Target file: [django_apps/shapez_solver/services/planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py), currently ~425 lines.
- External contract: [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py), [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py), [views.py](../../../../../django_apps/shapez_solver/views.py), and tests import `PlannerService`, `PlannerRequest`, `PlannerResult`, `UnsupportedTargetError` from `planner_service.py`.
- Internal responsibilities group into four: planner errors/DTOs, recursive solve orchestration (`solve_shape`), rule candidate generation (`try_*` family), shared assembly and shape helpers (`_build_operation_solution`, `_paint_shape`, `_split_halves`, etc.).
- Safest refactor: keep public types and import paths; move rule candidate generation and helpers to separate modules.
- Repository is dirty: [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py) and [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) import deleted `graph_builder`; run planner-specific tests separately to confirm refactor regression.
