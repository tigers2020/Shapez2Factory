# dead code cleanup research (2026-05-01)

- 사용자 요청은 죽은 파일과 중복 코드를 삭제하는 시퀀스 리팩토링이다.
- 현재 워크트리는 이미 여러 분리 리팩토링이 진행 중인 더티 상태다. 특히 [django_apps/shapez_solver/services/graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py) 는 삭제되었고, 대체 구현 [recipe_graph_builder.py](../../../../../django_apps/shapez_solver/services/recipe_graph_builder.py) 가 추가되어 있다.
- 런타임 경로를 보면 [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) 는 이미 [FactoryThroughputService](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) 를 사용하고 있고, 더 이상 [SolverService](../../../../../django_apps/shapez_solver/services/solver_service.py) 를 호출하지 않는다.
- 반면 [solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py) 와 [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) 는 같은 핵심 solve 파이프라인을 거의 중복으로 가진다: `PlannerService.solve_shape()` 호출, `OperationEngine.evaluate()` 검증, `RecipeGraphBuilder.build()` 호출, `SolveStep` 조립.
- `SolverService` 참조는 저장소 안에서 테스트에만 남아 있다. 확인된 경로는 [tests/unit/shapez_solver/test_solver_service.py](../../../../../tests/unit/shapez_solver/test_solver_service.py) 와 [tests/unit/shapez_core/test_shape_code_parser.py](../../../../../tests/unit/shapez_core/test_shape_code_parser.py) 이다.
- 따라서 현재 가장 큰 중복 제거 후보는 `solver_service.py` 자체이거나, 최소한 그 내부 solve 로직을 공용 helper 로 내리는 것이다.
- 프런트 쪽 [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 와 [shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) 는 하위 모듈 디렉터리의 얇은 entrypoint 로 바뀌었지만, 템플릿에서 직접 로드할 가능성이 있어 죽은 파일로 단정하면 위험하다. 이 둘은 현재 삭제 후보가 아니라 공개 진입점으로 보는 편이 안전하다.
- [django_apps/shapez_solver/services/graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py) 삭제는 이미 진행되었고, 남은 과제는 참조 정리와 테스트/호환 계층 축소다.
- 안전한 삭제 순서는 `graph_builder` 참조 완전 제거 확인 → `solver_service` 의 실제 호출자 제거 또는 shim 화 → 테스트를 새 서비스 기준으로 갱신 → 마지막에 죽은 파일 삭제 여부 결정 순서다.
- 리스크는 두 가지다.
  1. `solver_service.py` 가 저장소 밖에서 import되는 비공개 의존이 있을 수 있다.
  2. `test_solver_service.py` 는 단순 회귀 테스트이면서 동시에 이전 공개 계약을 문서화하는 역할도 하고 있어서, 삭제 시 테스트 의미도 재설계해야 한다.
