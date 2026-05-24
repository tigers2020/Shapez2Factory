# solver bundle overlay research
Date: 2026-05-03

## Scope

- 특정 패턴을 의미 단위로 묶는 `bundle_overlay` 설계 전, 현재 solver graph 생성과 렌더링 경계를 확인했다.
- 대상 macro phase는 `quad_stage`, `checker_stage`, `swap_stage`다.
- 이번 문서는 코드 변경 전 조사 결과이며, 원자 graph와 materialized graph의 의미를 바꾸지 않는 것을 전제로 한다.

## Current Graph Contract

- graph DTO는 `django_apps/shapez_solver/dto/solver_graph.py`의 `SolverGraph`, `SolverShapeNode`, `SolverOperationNode`, `SolverGraphEdge`가 중심이다.
- shape node는 `role`, `shape_code`, `quantity`, `produced_state`, batch metadata를 가진다.
- operation node는 `operation_type`, port count, icon, run metadata를 가진다.
- edge는 `from_id`, `to_id`, `kind`, `slot`, `label`만 가진다.
- `SolverGraph.group_annotation`은 선택 필드이고, 현재 graph JSON에는 `groups`로 직렬화된다.

## Materialized Graph

- `MaterializedGraphBuilder`는 target count와 base demands를 반영해 실제 생산 흐름을 node/edge 수량만큼 펼친다.
- materialized graph는 target/source quantity를 단일 숫자로만 표현하지 않고 batch item, operation run, unused output까지 포함한다.
- 따라서 materialized graph에서 노드를 실제로 합치면 수량, batch, unused output, target output count가 깨질 수 있다.
- 현재 builder는 graph 생성 뒤 `_with_group_annotation()`으로 operation 중심 group annotation을 붙인다.

## Existing Group Annotation

- `group_annotation_builder.py`는 operation 하나를 중심으로 input, output, boundary ref를 묶는다.
- `groups`의 주 목적은 프런트 레이아웃에서 operation card와 그 주변 shape card를 배경 박스로 안정적으로 배치하는 것이다.
- `groups.node_ownership`은 한 node를 한 group에 배정하는 projection에 가깝다.
- 이 구조는 operation run group에는 적합하지만, `checker_stage`와 `swap_stage`처럼 의미 단위가 겹치는 macro cover에는 맞지 않는다.

## Serialization And Frontend

- `view_graph_serialization.py`는 `nodes`, `edges`, `layout`, 선택적으로 `groups`를 내려보낸다.
- 프런트 graph renderer는 `solver_timeline/graph_markup.js`와 `solver_graph_layout.js`에서 `groups`를 읽어 group background와 boundary ref indicator를 그린다.
- detail panel은 선택 node id로 원본 `graph.nodes`와 `graph.edges`를 직접 조회한다.
- 따라서 bundle collapsed UI를 만들더라도 원본 graph는 보존하고, UI 전용 파생 graph 또는 overlay 렌더링 경로가 is required.

## Why Bundle Must Be Overlay

- `quad_stage`, `checker_stage`, `swap_stage`는 일반 operation 하나가 아니라 여러 operation과 shape를 관통하는 의미 단위다.
- 같은 node가 하위 준비 단계와 상위 macro stage에 동시에 속할 수 있다.
- strict partition 방식은 checker output을 swap input으로 쓰는 순간 소유권 충돌이 생긴다.
- bundle은 partition이 아니라 cover여야 하며, 내부 데이터는 overlap을 허용해야 한다.
- UI collapse에서만 `visible_bundle_id`를 선택하면 된다.

## Proposed Separation

| Structure | Responsibility | Overlap |
| --- | --- | --- |
| `nodes` / `edges` | 계산과 수량의 source of truth | 해당 없음 |
| `groups` | operation 중심 layout 보조 projection | 기본적으로 단일 ownership |
| `bundle_overlay` | quad/checker/swap 의미 단위 macro cover | 허용 |

## Detection Inputs

현재 DTO 기준으로 detector가 바로 쓸 수 있는 정보:

- operation node: `operation_type`
- shape node: `shape_code`, `role`, `produced_state`
- graph topology: input/output edge 방향

초기 구현에서 추가로 필요한 helper:

- node id별 incoming/outgoing edge index
- operation input shape와 output shape 추론
- `shape_code` parser 기반 quad-ready/checker/permutation 판정 함수

## Risks

- 기존 `groups` 키를 bundle 용도로 재사용하면 layout group과 macro bundle 의미가 섞인다.
- materialized graph를 물리적으로 축약하면 batch와 unused output 표현이 손상된다.
- detector가 앞에서부터만 탐색하면 checker처럼 결과 shape가 더 명확한 패턴에서 오탐이 늘 수 있다.
- swap 판정을 `operation_type == "swapper"`만으로 제한하면 shape permutation 기반 swap-like macro를 놓칠 수 있다.

## Conclusion

- 후속 구현은 기존 `groups`를 그대로 두고 새 `bundle_overlay`를 추가하는 방식이 가장 안전하다.
- bundle detection은 materialized graph 생성 이후 별도 pass로 실행한다.
- 원본 graph는 변경하지 않고 bundle id, macro type, member node ids, boundary edge refs, visible assignment만 annotation으로 내려보낸다.
