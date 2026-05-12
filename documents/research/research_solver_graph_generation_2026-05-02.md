# solver graph 생성 로직 리서치

날짜: 2026-05-02

## 범위

- 현재 solver graph 가 어떤 경로로 만들어지는지 코드 기준으로 추적한다.
- 대상은 요청 진입점, planner/throughput 계층, graph DTO 조립, JSON 직렬화, 프런트 런타임 레이아웃까지다.
- "어떤 해법을 찾는가" 전체보다, "찾아낸 해법을 어떤 graph 계약으로 바꾸는가"를 중심으로 본다.

## 한 줄 요약

현재 solver graph 는 아래 순서로 만들어진다.

1. `views.py` 가 요청에서 shape code 를 파싱한다.
2. `FactoryThroughputService` 가 target batch 와 base demand 를 계산한다.
3. `solve_recipe_pipeline()` 이 `PlannerService` 로 `SolvedRecipe` 를 만든다.
4. 같은 파이프라인 안에서 `RecipeGraphBuilder.build()` 가 `SolvedRecipe.recipes` 를 순회하며 `SolverGraph` DTO 를 만든다.
5. `serialize_solver_graph()` 가 shape node preview PNG URL 과 operation icon URL 을 붙여 API JSON 으로 직렬화한다.
6. 브라우저에서는 `solver_graph_layout.js` 가 받은 `nodes` 와 `edges` 로 좌표를 계산한다.

즉, 백엔드는 "그래프 구조"를 만들고, 프런트는 "좌표 레이아웃"만 계산한다.

## 1. 요청 진입점

진입점은 `django_apps/shapez_solver/views.py` 의 `solve_shape()` 다.

- 요청에서 `code` 를 꺼낸다.
- `parse_shape_code_list()` 로 파싱한다.
- 첫 번째 pattern 만 target 으로 사용한다.
- normalized code 와 다르면 warning 을 쌓는다.
- 이후 `FactoryThroughputService().solve(...)` 를 호출한다.

여기서 graph 는 아직 만들어지지 않는다. 이 계층은 입력 검증, warning 수집, 에러 응답 매핑만 담당한다.

## 2. throughput 단계에서 graph 생성 준비

`django_apps/shapez_solver/services/factory_throughput_service.py`

`FactoryThroughputService.solve()` 의 역할은 graph 자체를 직접 그리는 것이 아니라, graph builder 에 필요한 수량 문맥을 준비하는 것이다.

- `compute_factory_batch(target_shape)` 가 가능하면:
  - `target_count`
  - `base_demands`
  를 계산한다.
- 지원하지 않는 대상이면:
  - `target_count = 1`
  - `base_demands = ()`
  - warning 추가

그 다음 `solve_recipe_pipeline()` 에 아래 값을 넘긴다.

- `target_shape`
- `target_count`
- `base_demands`

즉 graph 안의 source 수량, target 라벨, target quantity 는 planner 가 아니라 throughput 단계에서 결정된다.

## 3. solve pipeline: 해법 검증 후 graph builder 호출

`django_apps/shapez_solver/services/solve_pipeline.py`

`solve_recipe_pipeline()` 흐름은 다음과 같다.

1. `PlannerService.solve_shape(target_shape, SolveContext())`
   - target 을 만드는 최적 `SolvedRecipe` 를 만든다.
2. `OperationEngine.evaluate(solved.recipes, solved.ref)`
   - recipe replay 결과가 정말 target 과 같은지 재검증한다.
3. 검증이 통과하면 `RecipeGraphBuilder.build(...)`
   - `SolvedRecipe` 를 `SolverGraph` 로 변환한다.
4. 별도로 `_build_steps(solved)` 로 타임라인용 step 목록도 만든다.

이 레이어의 중요한 점은 graph builder 가 planner 와 분리되어 있다는 점이다.

- planner 책임: 어떤 recipe DAG 를 선택할지 결정
- graph builder 책임: 선택된 recipe DAG 를 UI/API 계약용 graph DTO 로 변환

## 4. planner 가 graph builder 에 넘기는 데이터 구조

`django_apps/shapez_solver/domain/recipe.py`

graph builder 의 입력은 `SolvedRecipe` 다.

- `SolvedRecipe.ref`
  - 최종 target 이 어느 recipe output 인지 가리키는 포인터
- `SolvedRecipe.recipes`
  - `SourceRecipe | OperationRecipe` 의 튜플

핵심 타입:

- `SourceRecipe`
  - 원재료 source node 후보
- `OperationRecipe`
  - cutter, rotate, painter, stacker 같은 가공 노드 후보
- `RecipeRef`
  - 특정 recipe 의 몇 번째 output 을 참조하는지 나타냄

graph builder 는 별도 탐색을 하지 않고, 이 `recipes` 목록을 순회해서 shape node / operation node / edge 를 조립한다.

## 5. planner 가 `SolvedRecipe` 를 고르는 방식

`django_apps/shapez_solver/services/planner_service.py`

graph 모양을 이해하려면 planner 가 어떤 후보를 만들 수 있는지 알아둘 필요가 있다.

- direct source 면 `try_source()` 로 즉시 끝난다.
- 아니면 아래 rule 후보를 순서대로 시도한다.
  - rotation
  - stack layers
  - paint
  - assemble halves
  - assemble quadrants
  - cut from source
- 각 후보는 `OperationEngine.evaluate(...) == target` 인지 검증된다.
- 마지막에 `RecipeCost.as_sort_key()` 로 최소 cost 후보를 채택한다.

즉 graph 의 연산 종류와 분기 구조는 planner rule 세트에서 오고, graph builder 는 그 결과를 표현만 한다.

## 6. graph DTO 계약

`django_apps/shapez_solver/dto/solver_graph.py`

백엔드가 만드는 graph DTO 는 단순하다.

- `SolverGraph`
  - `nodes`
  - `edges`
  - `direction = "left-to-right"`
- `SolverShapeNode`
  - `role`: `source | intermediate | target`
  - `shape_code`, `label`, `preview_scene`, `reused_count`, `quantity`
- `SolverOperationNode`
  - `operation_type`, `label`, `icon`, `input_count`, `output_count`, `description`
- `SolverGraphEdge`
  - `from_id`, `to_id`, `kind`, `slot`, `label`

중요한 점은 이 DTO 에 좌표 정보가 없다는 것이다. 노드 위치는 프런트에서 계산한다.

## 7. `RecipeGraphBuilder` 의 실제 조립 순서

`django_apps/shapez_solver/services/recipe_graph_builder.py`

`RecipeGraphBuilder.build()` 는 아래 순서로 동작한다.

### 7.1 상태 초기화

먼저 `_build_state(...)` 로 내부 state 를 만든다.

- `nodes`, `edges`
- `seen_shape_nodes`
  - 같은 shape output node 중복 추가 방지
- `final_key`
  - 최종 target output key
- `used_output_keys`
  - 다른 연산 input 으로 실제 소비되거나 최종 target 인 output 목록
- `reused_counts`
  - 같은 output 이 여러 번 입력으로 참조된 횟수 기반 재사용 수
- `target_count`
- `base_quantity_by_shape`
  - `base_demands` 를 shape code -> 수량 map 으로 변환한 값

여기서 `final_key` 와 `used_output_keys` 가 target 판정, unused output 표시의 기준이 된다.

### 7.2 recipe 목록 순회

`for recipe in solved.recipes`

- `SourceRecipe` 이면 `_append_source_shape_node()`
- `OperationRecipe` 이면
  - `_append_operation_node()`
  - `_append_input_edges()`
  - `_append_output_shape_nodes_and_edges()`

즉 source 는 shape node 하나만 만들고, operation 은 "연산 노드 + 입력 edge + 출력 shape node + 출력 edge" 묶음으로 추가된다.

## 8. source shape node 생성 규칙

`_append_source_shape_node(state, recipe)`

ID 규칙:

- source shape node id 는 항상 `"{recipe.id}:shape:0"`

target 판정:

- `recipe_key = "{recipe.id}:0"`
- 이 값이 `state.final_key` 와 같으면 source 이면서 동시에 최종 target 이다.

필드 규칙:

- `role`
  - 최종 target 이면 `target`
  - 아니면 `source`
- `label`
  - target 이면 `Target` 또는 `Target xN`
  - 아니면 `recipe.label`
- `quantity`
  - target 이면 `target_count`
  - source 이면 `base_quantity_by_shape.get(shape_code, 1)`
- `reused_count`
  - 동일 output 이 여러 번 참조되면 `count - 1`
- `preview_scene`
  - `_serialize_shape_preview(shape)`

그래서 "source 하나로 바로 target 이 되는 문제"는 shape node 1개짜리 graph 로 끝난다.

## 9. operation node 생성 규칙

`_append_operation_node(state, recipe)`

연산 노드는 `OPERATION_CATALOG` 에서 메타데이터를 가져와 만든다.

- `id = recipe.id`
- `operation_type = recipe.operation_type.value`
- `label = recipe.label`
- `icon = operation.icon`
- `input_count`, `output_count`, `description`

즉 operation node 의 표시 정보는 recipe 객체와 operation catalog 의 결합 결과다.

## 10. input edge 생성 규칙

`_append_input_edges(state, recipe)`

각 input ref 마다 edge 하나를 만든다.

- `from_id = "{input.recipe_id}:shape:{input.output_index}"`
- `to_id = recipe.id`
- `kind = "input"`
- `slot = label = "Input A"`, `"Input B"` ...

중요한 점은 input edge 가 shape node 에서 operation node 로 향한다는 것이다.

## 11. output shape node 와 output edge 생성 규칙

`_append_output_shape_nodes_and_edges(state, recipe)`

각 output index 마다:

1. output shape node 추가 시도
2. operation -> shape output edge 추가

output key / id 규칙:

- `output_key = "{recipe.id}:{output_index}"`
- `output_node_id = "{recipe.id}:shape:{output_index}"`

shape node 필드 규칙:

- `role`
  - `output_key == final_key` 이면 `target`
  - 아니면 `intermediate`
- `label`
  - target 이면 `Target` 또는 `Target xN`
  - 아니면 `"Shape"`
- `quantity`
  - target 이면 `target_count`
  - intermediate 이면 `1`
- `reused_count`
  - `_compute_reused_counts()` 결과 반영
- `preview_scene`
  - `_serialize_shape_preview(output_shape)`

output edge 규칙:

- `from_id = recipe.id`
- `to_id = output_node_id`
- `kind = "output"`
- `slot = "Output A"`, `"Output B"` ...
- `label`
  - output 이 실제로 다른 곳에서 쓰이거나 최종 target 이면 `"Output A"`
  - 아니면 `"Output A (unused)"`

테스트에서 자주 보이는 `"Output B (unused)"` 는 바로 이 규칙에서 나온다.

## 12. reused count 계산 규칙

`_compute_reused_counts(solved)`

재사용 수는 "같은 output 이 operation input 으로 몇 번 소비되는가"를 기준으로 한다.

- 모든 `OperationRecipe.inputs` 를 순회하며 `"{recipe_id}:{output_index}"` 카운트
- 2번 참조되면 `reused_count = 1`
- 3번 참조되면 `reused_count = 2`

즉 표시값은 총 사용 횟수가 아니라 "첫 사용을 제외한 추가 재사용 횟수"다.

## 13. preview scene 생성 규칙

shape node 는 모두 `preview_scene` 을 가진다.

- graph builder 는 `_serialize_shape_preview(shape)` 로 scene 을 미리 넣는다.
- scene 안에는 `normalized_code` 와 `cells[]` 가 들어 있다.
- 각 cell 은 layer, quadrant, color, mesh/material/transform key 까지 포함한다.

이 scene 은 두 군데에서 쓰인다.

1. API payload 로 그대로 노출
2. `GraphPreviewRenderer.render(preview_scene)` 의 입력

즉 graph node preview 는 planner 산출물이 아니라 shape render scene 산출물이다.

## 14. API JSON 직렬화 단계

`django_apps/shapez_solver/view_graph_serialization.py`

`serialize_solver_graph(graph)` 는 `SolverGraph` DTO 를 최종 JSON 계약으로 바꾼다.

- `layout.direction`
  - 현재는 백엔드에서 항상 `"left-to-right"`
- `nodes`
  - shape / operation 별로 분기 직렬화
- `edges`
  - `from`, `to`, `kind`, `slot`, `label`

shape node 직렬화:

- `preview_renderer = get_graph_preview_renderer()`
- `graph_preview = preview_renderer.render(preview_scene)`
- 결과로
  - `preview_scene`
  - `preview_image_url`
  - `preview_alt`
  를 붙인다.

operation node 직렬화:

- `static("web/images/operations/...")` 로 icon URL 생성

즉 graph builder 는 "구조와 원시 preview scene" 까지 만들고, serializer 가 "브라우저가 바로 쓸 URL" 을 완성한다.

## 15. 최종 응답 payload 에서 graph 위치

`django_apps/shapez_solver/view_serialization.py`

`serialize_solver_result()` 는 solver 응답 전체를 만들고, 그 안에

- `steps`
- `base_demands`
- `warnings`
- `graph`

를 넣는다.

여기서 `graph` 는 `serialize_solver_graph(result.graph)` 결과다.

따라서 외부 API 계약의 graph 필드는 `FactoryThroughputResult.graph -> SolverGraph -> serialized graph dict` 의 2단계 변환 결과다.

## 16. 프런트에서 추가로 하는 일: 레이아웃 계산

`django_apps/web/static/web/js/solver_graph_layout.js`

백엔드는 노드 연결만 넘기고, 브라우저가 실제 좌표를 계산한다.

핵심 단계:

1. `computeNodeDepths(graph)`
   - edge 를 따라 DAG depth 계산
2. `groupNodeIdsByDepth(graph, depths)`
   - depth 별 column 그룹화
3. `orderNodeIdsByBarycenter(...)`
   - predecessor/successor barycenter 기준으로 column 내부 순서 재정렬
4. `computeVerticalTopPositions(...)`
   - 여러 sweep 으로 y 위치 compaction
5. `computeHorizontalPositions(...)`
   - predecessor 위치와 same-rank gap 을 고려해 x 위치 계산
6. `buildFinalGraphLayout(...)`
   - `positions`, `width`, `height`, `bounds` 산출

즉 현재 계약은:

- 백엔드: DAG 구조와 node metadata 제공
- 프런트: depth/barycenter 기반 grouped layout 계산

## 17. 테스트가 고정해 두는 graph 계약

현재 로직은 아래 테스트들로 보호된다.

- `tests/unit/shapez_solver/test_solver_service.py`
  - source-only graph
  - rotation / painter / stacker 포함 여부
  - target node 1개
  - unused output edge 라벨
  - auto batch 가 source quantity 와 target quantity 에 반영되는지
- `tests/integration/api/test_solver_api.py`
  - API payload 의 `graph.nodes` 구조와 target quantity / label
- `tests/integration/web/test_web_smoke.py`
  - `layout.direction == "left-to-right"`
  - graph node preview / operation icon 계약
  - 프런트가 `solver_graph_layout.js` 를 사용하는지
- `tests/unit/web/test_solver_graph_layout.py`
  - 프런트 grouped layout 알고리즘 자체의 결정성/배치 규칙

그래서 graph 관련 리팩토링을 할 때는 DTO 필드명뿐 아니라 아래 의미 계약도 깨지면 안 된다.

- target node 는 정확히 1개여야 한다.
- source quantity 는 base demand 에 의해 덮어써질 수 있다.
- intermediate quantity 는 현재 1이다.
- unused output 은 edge label 로 드러난다.
- 좌표는 서버가 아니라 클라이언트가 계산한다.

## 18. 현재 구조를 이해할 때 주의할 점

1. planner 와 graph builder 는 같은 것이 아니다.
   planner 는 정답 recipe 를 찾고, graph builder 는 그 결과를 시각화용 DTO 로 변환한다.
2. graph DTO 와 API JSON 도 같은 것이 아니다.
   preview PNG URL 과 static icon URL 은 serializer 단계에서 붙는다.
3. graph layout 은 백엔드 책임이 아니다.
   서버는 위치를 저장하지 않고, 프런트가 depth/barycenter 기반으로 계산한다.
4. `target_count` 는 graph 전체 quantity 표시에 강하게 관여한다.
   특히 target label 과 source quantity 가 throughput 계층의 계산 결과에 따라 달라진다.

## 19. 실무적으로 보면 수정 포인트는 여기다

- planner 규칙을 바꾸고 싶으면:
  - `django_apps/shapez_solver/services/planner_service.py`
  - `django_apps/shapez_solver/services/planner_rules.py`
- graph node/edge 규칙을 바꾸고 싶으면:
  - `django_apps/shapez_solver/services/recipe_graph_builder.py`
- API graph payload 필드를 바꾸고 싶으면:
  - `django_apps/shapez_solver/view_graph_serialization.py`
- 브라우저 배치만 바꾸고 싶으면:
  - `django_apps/web/static/web/js/solver_graph_layout.js`

## 결론

현재 solver graph 생성 로직의 핵심은 `SolvedRecipe` 를 중심으로 한 3단 변환이다.

1. planner 가 `SolvedRecipe` 를 만든다.
2. `RecipeGraphBuilder` 가 그것을 `SolverGraph` 로 바꾼다.
3. serializer 와 frontend 가 각각 "표시용 자산"과 "좌표"를 추가한다.

그래서 graph 문제를 디버깅할 때는 항상

- recipe 가 잘못 생성된 것인지
- graph builder 가 잘못 매핑한 것인지
- serializer 가 preview/icon 을 잘못 붙인 것인지
- frontend layout 이 잘못 배치한 것인지

를 나눠서 보는 편이 가장 빠르다.
