# Plan: solver bundle overlay
Date: 2026-05-03

Related research: [research_solver_bundle_overlay_2026-05-03.md](./research_solver_bundle_overlay_2026-05-03.md)

## Goal

- materialized graph의 원자 node/edge는 그대로 preserved.
- `quad_stage`, `checker_stage`, `swap_stage`를 별도 `bundle_overlay` annotation으로 표현한다.
- 기존 `groups`는 operation 중심 layout projection으로 유지하고, bundle은 의미 단위 macro cover로 분리한다.

## Data Model

후속 구현에서 새 DTO 모듈을 added.

```python
@dataclass(frozen=True, slots=True)
class GraphBundle:
    """solver graph 위에 표시할 의미 단위 macro 묶음."""

    id: str
    macro_type: str
    label: str
    member_node_ids: frozenset[str]
    input_boundary_edge_ids: tuple[str, ...]
    output_boundary_edge_ids: tuple[str, ...]
    anchor_node_id: str
    depth: int
    score: float


@dataclass(frozen=True, slots=True)
class BundleOverlay:
    """원본 graph를 변경하지 않는 bundle annotation 결과."""

    bundles: tuple[GraphBundle, ...]
    node_to_bundle_ids: dict[str, frozenset[str]]
    visible_node_to_bundle_id: dict[str, str]
```

- edge에는 현재 id가 없으므로 serializer에서는 stable edge ref를 `"{from_id}->{to_id}:{kind}:{slot}"` 형태로 만들거나, 후속 구현에서 `SolverGraphEdge.id` 추가 여부를 별도 승인받는다.
- 이번 구현안의 기본값은 DTO signature 변경을 줄이기 위해 serializer/helper 내부 stable edge ref를 사용한다.

## Detection Pipeline

`MaterializedGraphBuilder`와 `RecipeGraphBuilder`가 graph를 만든 뒤 다음 pass를 붙인다.

```text
SolverGraph
  -> build_group_annotation()
  -> build_bundle_overlay()
  -> serialize_solver_graph()
```

Implementation candidates:

- `BundlePatternDetector` protocol: `macro_type`, `detect(graph) -> list[GraphBundle]`
- `QuadStageDetector`: source/base에서 시작해 cut, rotate, stacker, painter 계열을 따라 quad-ready shape까지 묶는다.
- `CheckerStageDetector`: checker output shape를 만드는 anchor operation에서 backward collect한다.
- `SwapStageDetector`: `operation_type == "swapper"` 또는 permutation-only output을 anchor로 backward collect한다.

초기 detector는 보수적으로 동작한다.

- 명확히 판정 가능한 bundle만 생성한다.
- 판정 불가 shape는 bundle을 만들지 않는다.
- TODO 주석으로 checker 휴리스틱 고도화 지점을 표시한다.

## Resolver Rules

- bundle은 partition이 아니라 cover다. 한 node는 여러 bundle에 속할 수 있다.
- `node_to_bundle_ids`에는 모든 membership을 보존한다.
- UI collapse용 대표 bundle은 resolver가 선택한다.

우선순위:

```text
swap_stage > checker_stage > quad_stage
```

selection key:

```python
(macroPriority[macro_type], score, len(member_node_ids))
```

동점이면 `bundle.id` 사전순으로 고정해 deterministic output을 보장한다.

## JSON Contract

기존 `nodes`, `edges`, `groups`는 do not change.

```json
{
  "nodes": [
    {
      "id": "materialized:swapper:run:1",
      "kind": "operation",
      "operation": {"type": "swapper"},
      "bundle_ids": ["bundle_checker_x", "bundle_swap_y"],
      "visible_bundle_id": "bundle_swap_y"
    }
  ],
  "bundle_overlay": {
    "bundles": [
      {
        "id": "bundle_swap_y",
        "macro_type": "swap_stage",
        "label": "Swap",
        "member_node_ids": ["shape:a", "materialized:swapper:run:1", "shape:b"],
        "input_boundary_edge_ids": ["shape:a->materialized:swapper:run:1:input:Input A"],
        "output_boundary_edge_ids": ["materialized:swapper:run:1->shape:b:output:Output A"],
        "anchor_node_id": "materialized:swapper:run:1",
        "depth": 0,
        "score": 1.0
      }
    ],
    "node_to_bundle_ids": {
      "materialized:swapper:run:1": ["bundle_checker_x", "bundle_swap_y"]
    },
    "visible_node_to_bundle_id": {
      "materialized:swapper:run:1": "bundle_swap_y"
    }
  }
}
```

## UI Follow-up

Phase 1은 JSON overlay만 제공한다.

Phase 2에서 collapsed graph를 만든다.

- bundle id별 super-node를 생성한다.
- bundle 내부 edge는 숨긴다.
- boundary edge만 외부에 노출한다.
- click/detail panel에서는 bundle summary와 member atomic nodes를 보여준다.
- expanded mode에서는 기존 atomic graph renderer를 그대로 사용한다.

## Test Plan

- DTO 단위 테스트: `GraphBundle`, `BundleOverlay` 생성과 immutability 확인
- detector synthetic graph 테스트:
  - source -> cutter -> rotate -> stacker -> quad-ready shape
  - two branches -> stacker/checker output
  - checker output -> swapper -> target
- resolver 테스트:
  - 같은 node가 quad/checker/swap에 모두 속할 때 `swap_stage` 선택
  - score와 member count tie-break deterministic 확인
- serializer/API 테스트:
  - 기존 `groups`가 유지된다.
  - 새 `bundle_overlay`가 추가된다.
  - node payload에 `bundle_ids`, `visible_bundle_id`가 포함된다.
- UI 후속 테스트:
  - collapsed mode에서 super-node와 boundary edge만 렌더링
  - expanded mode에서 원자 node/edge가 보존됨

## Validation Commands

후속 구현 done 후 렉스가 아래 순서로 검증한다.

```text
pytest
ruff check .
mypy .
black .
```

CI에서는 파일 변경이 없는 `black --check .`를 사용한다.

## Migration

- DB model 변경이 없으므로 migration은 필요 없다.
- 예상 변경은 DTO, service pass, serializer, frontend renderer/test에 한정된다.

## CURSOR_MEMO Update

- `documents/CURSOR_MEMO.md`가 존재하므로, 이번 결정은 짧게 added.
- 기록 내용은 "bundle은 graph 병합이 아니라 overlay이며, 기존 groups와 분리한다"로 제한한다.

## Assumptions

- checker 판정은 초기 구현에서 shape parser 기반 휴리스틱으로 start with.
- 정확한 shapez 2 checker rule 고도화와 config 파일화는 Phase 3로 분리한다.
- 후속 구현 전 사람 승인을 다시 받는다.
