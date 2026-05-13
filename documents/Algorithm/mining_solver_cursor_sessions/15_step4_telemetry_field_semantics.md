# STEP4 텔레메트리 필드 의미 (계약 보조, CANON)

작성: STEP4 NDJSON·`step4_route_failure_detail` 해석 시 혼동 방지. 구현 정본은 코드와 단위 테스트
(`tests/unit/shapez_asteroid/test_step4_telemetry_regression_gates.py`)이다.

## `external_goal_count` (상위 detail / 미러)

- **정의**: `len(goal_cells ∩ margin_cells)` — 즉 **당시 Dijkstra에 사용된 `goal_cells`** 과
  `exterior_margin_cells`로 계산된 margin 집합의 교집합 크기이다.
- **아닌 것**: “외곽 margin goal 정책으로 구성한 좌표 개수”만을 뜻하지 않는다. `goal_cells`에
  margin 좌표가 포함되지 않으면 0이 될 수 있다 (예: `fluid_pipe` 분기에서 primary goal만
  쓰는 단계, 또는 margin 집합 자체가 비어 있는 경우).

## `existing_trunk_goal_count`

- **정의**: `len(trunk_cells)` — **현재 작업 맵**에서 exterior에 도달하는 same-kind transport
  셀 수이다. §08 `trunk_seed_candidate_count`(margin ∪ ELA 힌트)와 독립이다.

## `trunk_seed_candidate_count`

- **정의**: 해당 `transport_kind`에 대해 `build_trunk_seed_candidates_by_kind`가 만든 후보
  집합 크기(margin ∪ `trunk_seed_cell_union` 힌트). margin·힌트가 모두 비면 0이다.

## `search_mode` vs `goal_ordering_mode`

- **`search_mode`**: STEP4 merge 루프에서 `search_stats`에 기록되는 **경로/계약 표식**으로,
  현재 기본값은 `goal_cells_union_legacy`이다 (Dijkstra가 `goal_cells` 집합 종료를 쓰는 경로).
- **`goal_ordering_mode`**: `merge_goal_union_meta`가 반환하는 메타의 `mode`로, goal 우선
  순위(티어·Manhattan·lex)는 여기에 해당한다 (예: `trunk_manhattan_margin_lex`).
- 두 값을 동일하게 해석하면 안 된다. 리팩터·대시보드에서는 **둘 다** 노출하는 것을 권장한다.

## NDJSON `step4_route_failure_detail` 이벤트

- `run_step4_merge_aware_routing` 종료 시 `failures` 행마다 한 번 `debug_log_event`가 호출된다.
- `attempt_index`는 실패 행의 `extractor_id`별 순번으로 스탬프된다 (`placement_id`와 다를 수 있음).

## 관련 코드

- `external_goal_count`: `step4_route_failure_detail.build_step4_route_failure_detail`
- margin·seed·raw goal: `step4_goal_trunk_seed.py`
- goal union·ordering meta: `step4_search_diagnostics.merge_goal_union_meta`
- fluid primary / margin fallback: `step4_merge_routing.py` 메인 루프
