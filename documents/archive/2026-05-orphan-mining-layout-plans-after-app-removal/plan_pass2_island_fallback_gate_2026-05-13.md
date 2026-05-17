# Pass2 island fallback gate 축소 플랜 (2026-05-13)

## 배경

`latest.ndjson` 기준 STEP4 telemetry alias 문제는 해소되었고, 남은 실패는 `fluid_pipe`
Pass2 placement가 STEP4에서 기존 same-kind trunk goal에 도달하지 못해 rollback되는 문제다.

관측된 핵심 패턴:

- Pass2 probe: `transport_cells_before_island_fallback`으로 `final_goal_count`가 생김.
- STEP4 실패: `existing_trunk_goal_count > 0`, `reachable_existing_trunk_count == 0`.
- `exterior_margin_cell_count == 0`, `trunk_seed_candidate_count == 0`.
- 같은 9개 placement가 STEP4 재진입 때문에 두 번 기록됨.

## 범위

1. `existing_layout_analysis`가 있는 Pass2 probe에서 canonical STEP4 goal이 비어 있고
   `transport_cells_before_island_fallback`만 목표를 만든 경우 placement commit을 거부한다.
2. 기존 telemetry key 이름은 변경하지 않는다.
3. STEP4 재진입 해석을 위해 `step4_reentry_index`만 추가한다.
4. Dijkstra 동작과 STEP4 route cost는 변경하지 않는다.

## 최소 구현

- `pass12_bundle_commit.py`
  - Pass2 probe 직후 `goal_trace`를 검사한다.
  - `fallback_goal_source == "transport_cells_before_island_fallback"`이고,
    `raw_goal_count == 0`, `trunk_reaching_probe_count == 0`,
    `exterior_margin_cell_count == 0`, `existing_layout_analysis`가 있으면 reject한다.
- `solver_pipeline/recovery_orchestrator.py`, `solver_pipeline/step4.py`,
  `step4/step4_merge_routing.py`
  - 첫 STEP4는 `step4_reentry_index=0`, recovery 재진입은 `1`로 전달한다.
  - `step4_completed`와 `step4_route_failure_detail`에 같은 값을 싣는다.

## 테스트

- Pass2 fluid fixture형 단위 테스트:
  - `existing_layout_analysis=None`인 기존 fallback 허용 케이스는 유지한다.
  - `existing_layout_analysis`가 있고 canonical goal 없이 fallback만 있는 경우 reject한다.
- STEP4 telemetry 단위 테스트:
  - 강제 실패 경로에서 failure detail에 `step4_reentry_index`가 노출되는지 확인한다.
