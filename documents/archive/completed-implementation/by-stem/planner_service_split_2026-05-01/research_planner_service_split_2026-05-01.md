# planner_service split research (2026-05-01)

- 대상 파일은 [django_apps/shapez_solver/services/planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py) 이고 현재 425줄 규모다.
- 외부 계약은 [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py), [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py), [views.py](../../../../../django_apps/shapez_solver/views.py), 테스트들이 `PlannerService`, `PlannerRequest`, `PlannerResult`, `UnsupportedTargetError` 를 `planner_service.py` 에서 import하는 점이다.
- 내부 책임은 4묶음이다: planner 에러/DTO, recursive solve orchestration (`solve_shape`), 규칙 후보 생성 (`try_*` 계열), 공통 조립 및 shape helper (`_build_operation_solution`, `_paint_shape`, `_split_halves` 등).
- 리팩토링은 공개 타입과 import 경로를 유지하면서 규칙 후보 생성과 helper 를 별도 모듈로 옮기는 형태가 가장 안전하다.
- 현재 저장소는 [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py), [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) 가 삭제된 `graph_builder` 를 import하는 더티 상태라, planner 전용 테스트를 별도로 돌려 리팩토링 회귀를 확인하는 것이 필요하다.
