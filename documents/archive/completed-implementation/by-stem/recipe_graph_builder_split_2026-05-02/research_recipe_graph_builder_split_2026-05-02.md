# recipe_graph_builder split research (2026-05-02)

- 대상 파일은 [django_apps/shapez_solver/services/recipe_graph_builder.py](../../../../../django_apps/shapez_solver/services/recipe_graph_builder.py) 이다.
- 현재 책임은 4묶음이다.
  1. recipe graph orchestration (`RecipeGraphBuilder.build`)
  2. source/operation/output node 초안 조립
  3. input/output edge 조립
  4. shape preview scene serialization
- 외부 호출자는 현재 [solve_pipeline.py](../../../../../django_apps/shapez_solver/services/solve_pipeline.py) 의 `RecipeGraphBuilder().build()` 한 곳뿐이다.
- 테스트는 직접 `RecipeGraphBuilder` 를 호출하지 않지만, [tests/unit/shapez_solver/test_solver_service.py](../../../../../tests/unit/shapez_solver/test_solver_service.py), [tests/unit/shapez_solver/test_factory_throughput_service.py](../../../../../tests/unit/shapez_solver/test_factory_throughput_service.py), [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py) 가 graph node role, label, quantity, unused output edge 같은 결과 계약을 검증한다.
- 지금 구조에서 가장 중복/응집도 문제가 큰 지점은 `build()` 안에 source node 생성, operation node 생성, output shape node 생성, edge 생성이 한 루프에 함께 섞여 있는 부분이다.
- `base_demands` 인자는 현재 `del base_demands` 로 무시된다. 이건 미래 확장용 흔적으로 보이지만, 현재 함수 시그니처 호환을 깨지 않으려면 당장은 유지하는 편이 안전하다.
- 안전한 분리 방식은 공개 class 이름은 유지하고, 내부 helper 를 다음처럼 분리하는 것이다.
  1. recipe usage analysis (`used_output_keys`, `reused_counts`)
  2. source node append helper
  3. operation node append helper
  4. output shape node append helper
  5. preview serialization helper
- 이렇게 하면 `RecipeGraphBuilder.build()` 는 루프 orchestration 만 남고, 규칙 자체는 바꾸지 않으면서 읽기/수정 비용을 줄일 수 있다.
