# STEP4 `no_route_exhausted` 샘플 리포트 (진단 전용)

**대상 로그:** `var/asteroid_mining_layout_debug/latest.ndjson` (run_id `d74e60416148` 등 동일 구조 NDJSON)  
**솔버 동작 변경 없음.** 아래 표·샘플은 NDJSON의 `routing_failures[]` + `step4_route_failure_diagnostic` / `step4_route_failure_detail`에서 추출했다.

## 질문별 요약

| 질문 | 결론 |
|------|------|
| 실패가 **stub 국소 탈출(geometry/corridor)** 위주인가? | **아니다.** `breaker_category`는 모두 `trunk_union_goals_unreachable_from_stub`이다. 이웃 `blocked_reason_near_stub`에 `blocked`/`ok`가 섞인 경우가 많지만, **외곽 margin goal 수(`exterior_goal_count`)가 0이고 trunk goal만 다수**인 패턴으로 분류된다. |
| 실패가 **trunk 토폴로지 상 stub에서 union 도달 불가** 위주인가? | **예.** 위와 동일하게 6건 전부 `trunk_union_goals_unreachable_from_stub`이다. `goal_count` 85~93, `existing_trunk_goal_count` 동일, `exterior_goal_count` 0. |
| 실패가 **search-budget** 관련 위주인가? | **아니다.** 샘플의 `classifier_inputs.stop_reason`은 null이고, `failure_reason`은 `no_route_exhausted`(탐색 소진)이나 **집계 축의 `search_budget_exhausted`와는 구분**된다. `route_length_ratio_exceeded`도 null. |
| 실패가 **hard-protected** 위주인가? | **아니다.** `solver_summary.step4_no_route_exhausted_breakdown`의 `by_protected_hard_count`는 전부 `"0"`이며, 이웃 전부 `hard_protected` 패턴도 아니다. |

## NDJSON에서의 출처

- `data` 트리 안의 객체에 `routing_failures` 배열이 붙는 trace 행이 있다.
- 각 실패 행에 `step4_route_failure_diagnostic`(`failure_reason`, goal 수, `stub_role` 등)과 `step4_route_failure_detail`(`blocked_reason_near_stub`, `nearest_existing_transport_distance` 등)이 함께 있다.
- 동일 `placement_id`가 **두 번** 등장할 수 있어, 샘플 추출 시 **`placement_id` 기준 중복 제거** 후 6건이 `step4_no_route_exhausted_breakdown.count`와 맞는다.

## 대표 샘플 (최대 5건)

다음 JSON은 `python scripts/debug/extract_step4_no_route_exhausted_samples.py` 출력을 그대로 옮긴 것이다.

```json
[
  {
    "placement_id": "p2-000059",
    "placement_pass": "pass2",
    "extractor_cell": [-2, -5],
    "stub_cell": [-1, -5],
    "transport_kind": "fluid_pipe",
    "failure_reason": "no_route_exhausted",
    "breaker_category": "trunk_union_goals_unreachable_from_stub",
    "nearest_transport_hops": 2,
    "goal_count": 85,
    "exterior_goal_count": 0,
    "existing_trunk_goal_count": 85,
    "expanded_nodes": 6,
    "blocked_reason_near_stub": [
      {"cell": [1, -5], "reason": "blocked"},
      {"cell": [-2, -5], "reason": "blocked"},
      {"cell": [-1, -4], "reason": "ok"},
      {"cell": [-1, -6], "reason": "ok"}
    ],
    "stub_role": "inferred",
    "expected_stub_role": "pipe",
    "classifier_inputs": {
      "goal_count": 85,
      "exterior_goal_count": 0,
      "existing_trunk_goal_count": 85,
      "stub_cell_role_ok": false,
      "nearest_transport_hops": 2,
      "stop_reason": null,
      "last_error": "no_route_exhausted",
      "route_length_ratio_exceeded": null
    }
  },
  {
    "placement_id": "p2-000062",
    "placement_pass": "pass2",
    "extractor_cell": [-1, -2],
    "stub_cell": [1, -2],
    "transport_kind": "fluid_pipe",
    "failure_reason": "no_route_exhausted",
    "breaker_category": "trunk_union_goals_unreachable_from_stub",
    "nearest_transport_hops": 9,
    "goal_count": 93,
    "exterior_goal_count": 0,
    "existing_trunk_goal_count": 93,
    "expanded_nodes": 33,
    "blocked_reason_near_stub": [
      {"cell": [2, -2], "reason": "ok"},
      {"cell": [-1, -2], "reason": "blocked"},
      {"cell": [1, -1], "reason": "blocked"},
      {"cell": [1, -3], "reason": "ok"}
    ],
    "stub_role": "inferred",
    "expected_stub_role": "pipe",
    "classifier_inputs": {
      "goal_count": 93,
      "exterior_goal_count": 0,
      "existing_trunk_goal_count": 93,
      "stub_cell_role_ok": false,
      "nearest_transport_hops": 9,
      "stop_reason": null,
      "last_error": "no_route_exhausted",
      "route_length_ratio_exceeded": null
    }
  },
  {
    "placement_id": "p2-000055",
    "placement_pass": "pass2",
    "extractor_cell": [-4, 0],
    "stub_cell": [-4, 1],
    "transport_kind": "fluid_pipe",
    "failure_reason": "no_route_exhausted",
    "breaker_category": "trunk_union_goals_unreachable_from_stub",
    "nearest_transport_hops": 7,
    "goal_count": 93,
    "exterior_goal_count": 0,
    "existing_trunk_goal_count": 93,
    "expanded_nodes": 34,
    "blocked_reason_near_stub": [
      {"cell": [-3, 1], "reason": "ok"},
      {"cell": [-5, 1], "reason": "blocked"},
      {"cell": [-4, 2], "reason": "blocked"},
      {"cell": [-4, 0], "reason": "blocked"}
    ],
    "stub_role": "inferred",
    "expected_stub_role": "pipe",
    "classifier_inputs": {
      "goal_count": 93,
      "exterior_goal_count": 0,
      "existing_trunk_goal_count": 93,
      "stub_cell_role_ok": false,
      "nearest_transport_hops": 7,
      "stop_reason": null,
      "last_error": "no_route_exhausted",
      "route_length_ratio_exceeded": null
    }
  },
  {
    "placement_id": "p2-000063",
    "placement_pass": "pass2",
    "extractor_cell": [1, 3],
    "stub_cell": [2, 3],
    "transport_kind": "fluid_pipe",
    "failure_reason": "no_route_exhausted",
    "breaker_category": "trunk_union_goals_unreachable_from_stub",
    "nearest_transport_hops": 4,
    "goal_count": 93,
    "exterior_goal_count": 0,
    "existing_trunk_goal_count": 93,
    "expanded_nodes": 43,
    "blocked_reason_near_stub": [
      {"cell": [3, 3], "reason": "blocked"},
      {"cell": [1, 3], "reason": "blocked"},
      {"cell": [2, 4], "reason": "ok"},
      {"cell": [2, 2], "reason": "blocked"}
    ],
    "stub_role": "occupied",
    "expected_stub_role": "pipe",
    "classifier_inputs": {
      "goal_count": 93,
      "exterior_goal_count": 0,
      "existing_trunk_goal_count": 93,
      "stub_cell_role_ok": false,
      "nearest_transport_hops": 4,
      "stop_reason": null,
      "last_error": "no_route_exhausted",
      "route_length_ratio_exceeded": null
    }
  },
  {
    "placement_id": "p2-000060",
    "placement_pass": "pass2",
    "extractor_cell": [-2, 3],
    "stub_cell": [-2, 4],
    "transport_kind": "fluid_pipe",
    "failure_reason": "no_route_exhausted",
    "breaker_category": "trunk_union_goals_unreachable_from_stub",
    "nearest_transport_hops": 5,
    "goal_count": 93,
    "exterior_goal_count": 0,
    "existing_trunk_goal_count": 93,
    "expanded_nodes": 44,
    "blocked_reason_near_stub": [
      {"cell": [-1, 4], "reason": "ok"},
      {"cell": [-3, 4], "reason": "ok"},
      {"cell": [-2, 5], "reason": "blocked"},
      {"cell": [-2, 3], "reason": "blocked"}
    ],
    "stub_role": "inferred",
    "expected_stub_role": "pipe",
    "classifier_inputs": {
      "goal_count": 93,
      "exterior_goal_count": 0,
      "existing_trunk_goal_count": 93,
      "stub_cell_role_ok": false,
      "nearest_transport_hops": 5,
      "stop_reason": null,
      "last_error": "no_route_exhausted",
      "route_length_ratio_exceeded": null
    }
  }
]
```

**참고:** `detail`의 `external_goal_count`는 diagnostic의 `exterior_goal_count`와 동일 역할로 0에 가깝다(본 로그에서는 margin goal 부재).

## Series 3 구현 방향 권고

1. **우선:** `documents/plans/plan_step4_no_route_exhausted_recovery_2026-05-12.md`의 **Case A(bounded local bridge)** — trunk-only goal union에 stub이 graphically 막혀 있지 않아도 **탐색 공간에서 연결되지 않는** 경우를 줄이는 쪽.
2. **Pass2/Pass3/P4/Reclaim 변경은 후순위**로 두고, STEP4 내부 복구·진단 보강으로 범위를 제한한다.
3. **`stub_cell_role_ok: false`**가 공통이므로, Series 3에서 bridge/재시도 시 **동종 transport role 정합**을 명시적으로 검증하는 trace를 추가하는 것이 안전하다(기존 키 이름 변경 없이).

## 재생성 명령

```text
python scripts/debug/extract_step4_no_route_exhausted_samples.py
python scripts/debug/extract_step4_no_route_exhausted_samples.py --path var/asteroid_mining_layout_debug/latest.ndjson --limit 5
```

중복 행까지 보고 싶으면 `--no-dedupe`.

## 검증

- 본 변경: **문서 + `scripts/` 도구**만. pytest 생략.
- `ruff check scripts/debug/extract_step4_no_route_exhausted_samples.py` 통과.
