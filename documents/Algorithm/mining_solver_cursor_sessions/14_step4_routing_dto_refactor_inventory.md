# STEP4 라우팅 DTO 리팩터 — 파라미터·상태 인벤토리 (Phase 0)

작성 목적: 긴 시그니처·반복 kwargs를 `Step4RoutingContext` / `Step4MutableState` / `Step4StubRouteJob` / 검색 스냅샷 / Trace 전용으로 분류한다.

## 네이밍·공개 계약 (Phase 0 결론)

| 항목 | 결정 |
|------|------|
| 공개 STEP4 출력 | 기존 [`Step4RoutingResult`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_contracts.py) 유지 |
| 내부 전용 | `Step4RoutingContext`(읽기 위주), `Step4MutableState`(런타임), `Step4StubRouteJob`(stub 1건), `Step4SearchSnapshot`(실패 상세·진단용 한 번의 탐색 스냅샷) |
| placement | 런타임은 `dict[str, PlacementCommitRecord]`; 최종 `Step4RoutingResult.placement_commit_by_id`는 기존처럼 `dict[str, str]` 직렬화 |
| `SolverRunContext` | 레이아웃 패키지 내 단일 클래스 없음 — Pass12/파이프라인에서 `run_step4_merge_aware_routing`으로 **projection** |

## 판정 기준

- 위치 인자 + kwonly 합계 **> 5** 이거나, 동일 kwargs 묶음이 **3+** 함수에 반복되면 표에 포함.

## 핵심 호출부

| 파일 | 함수 | 파라미터 요약 | 분류 |
|------|------|---------------|------|
| [step4_merge_routing.py](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py) | `run_step4_merge_aware_routing` | `map_after_pass2`, `final_mining_map`, `is_external`, `placement_records`, `force_route_attempt_placement_ids`, `mutate_input_map`, `existing_layout_analysis`, `hard_protected_cells` | Context 일부 + 진입 맵; 가변 `cells`/`work_records`는 MutableState |
| [solver_pipeline/step4.py](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/step4.py) | (STEP4 호출) | 위와 동일 kwargs 전달 | Orchestration → projection 지점 |

## STEP4 내부 — 긴 시그니처·반복 kwargs

| 파일 | 함수 | 개수(대략) | Context | MutableState | Job | Attempt/스냅샷 | TraceOnly |
|------|------|------------|---------|--------------|-----|----------------|-----------|
| step4_route_failure_detail.py | `build_step4_route_failure_detail` | 20+ kwonly | mineable, asteroid, is_external, cheap_reuse | cells | placement_id, ext, stub, tk | blocked, trunk, goals, transport_now, search_stats | forced_last_error, probe |
| step4_failed_pass2_route_recovery.py | `try_step4_failed_pass2_route_recovery` | 16 kwonly | mineable, asteroid, is_external, cheap_reuse | cells, committed_trunk, trunk_seed | ext, stub, tk, rec | blocked(내부), goals | dijkstra_fn |
| step4_local_bridge_recovery.py | `try_step4_local_bridge_recovery` | 22 kwonly | 동左 | cells, committed_trunk, trunk_seed | ext, stub, tk, rec | blocked, trunk, goals, detail, search_stats | meta |
| step4_dijkstra.py | `dijkstra_route_step4` | 1 + 10 kwonly | mineable, asteroid, is_external | cells | stub_cell | blocked, trunk, goal_cells, search_stats | margin_cells, cheap_reuse |
| step4_trunk_load.py | `build_step4_trunk_load` | 9 kwonly | — | trunk hits, visits, committed, per-kind sets | — | p2c_metrics | trace dict merge |
| step4_merge_routing.py | (메인 루프 내 블록) | 반복: `mineable, asteroid, is_external, cells, cheap_reuse_cells, hard_extras` | Context + State | `(ext_cell, stub_cell, tk, placement_id)` 튜플 = Job | 매 iteration `blocked`, `trunk_cells`, `goal_cells`, `search_stats` | NDJSON은 본 루프 밖 `debug_log_event` |

## routing_cells / reclaim

| 파일 | 함수 | 비고 |
|------|------|------|
| routing_cells.py | `collect_routing_jobs(cells)` | Job 리스트 생성; MutableState.cells 입력 |
| reclaim_corridors.py | `merge_step4_corridor_routing_mapping` 등 | `routing_state`·`trunk_load` **출력 계약** — 알고리즘 입력으로 끌어들이지 않음 |

## `search_stats` / `detail` dict

- **입력 분기**: `build_step4_route_failure_detail` 등이 `stop_reason` 등을 읽음 → Attempt/스냅샷 측에 두고, 알고리즘은 구조체만 갱신.
- **출력 전용**: 루프 내 `search_diag_samples` 축적 → Trace/요약.

## 권장 리팩터 순서 (요약)

1. 모델·빌더 도입, `run_step4_merge_aware_routing` 내부에서 `ctx`/`state` 사용.
2. 실패 상세·복구·다익스트라 호출을 `ctx`+`state`+`job`(+ `Step4SearchSnapshot`)로 축소.
3. `apply_placement_commit_state_transition` 호출을 `Step4MutableState` 메서드로 일원화.
4. `Step4TrunkLoadRuntime`(가칭)으로 trunk edge·visit 누적과 `build_step4_trunk_load` 직전 직렬화 분리.
