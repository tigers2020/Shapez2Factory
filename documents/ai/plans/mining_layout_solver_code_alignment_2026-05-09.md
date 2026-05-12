# 소행성 채굴 레이아웃 솔버: 코드 기준 정합 (2026-05-09)

외부 zip/구버전 파일명(`solve_pipeline.py`, `beam_placement.py`, `astar_router.py`)이 아니라 **현재 레포** 기준으로 파이프라인·타임라인·비용 계층을 정리한다.

## 모듈 맵

| 역할 | 경로 |
|------|------|
| 타임라인 오케스트레이션 | `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py` — `build_solver_timeline` |
| 입력 파싱 | `mining_map_input.py` — `parse_mining_map_inputs` |
| Extension 트리 (최대 3, 55 canonical) | `placement.py` — `enumerate_extension_trees`, `select_best_extension_tree_for_pass2`, `place_tree_bundle` |
| Pass2 void spine | `pass2_spine.py` |
| Pass3 가중 라우팅·커밋 | `pass3_transport.py` — `reconstruct_mining_priority_transport` |
| 철거/머지 repair 가중 경로 | `weighted_routing.py` + `cost_grid.py` |
| NDJSON 알고 trace | `solver_trace.py` (환경 `SHAPEZ_SOLVER_ALGO_DEBUG` 등) |
| Copy decode | `django_apps/shapez_core/services/shapez_copy_decode.py` |

## `build_solver_timeline` 순서 (요약)

1. `solver_init` — 입력 `mining_map` 스냅샷  
2. `solver_exit_anchor` — 앵커(외부 trunk 방향·margin) 포함 베이스 맵  
3. `solver_pass1_bundle_*` — 경계 스캔, **선형** `place_bundle` (`use_tree_bundle=False`)  
4. Pass2 spine — void 복도·`solver_pass2_bundle_*` 프레임  
5. `solver_pass2_bundle_*` — 내부 후보 스캔, **트리** 번들  
6. premerge `solver_pass3_transport_reconstruction_premerge` — Pass3 재구성 시도·언블록 루프  
7. `solver_merge_*` / repair / `solver_repair_path` / `solver_demolition` / `solver_corridor_reserved` — 머지·예산 복구  
8. `solver_pass3_transport_reconstruction` — post-merge Pass3  
9. (조건부) `solver_pass3_bundle_*` + `solver_pass3_transport_reconstruction_final`  
10. `solver_validate` — 연결성 검사 스냅샷  
11. 실패 시 `solver_partial_failure`

동적 id: `solver_pass{N}_bundle_{idx}`, `solver_merge_{n}`.

## API 타임라인 프레임 계약

각 원소는 대략 다음 형태다.

- `id` (str): 위 목록 중 하나  
- `summary`: UI용 요약  
- `mining_map`: 셀 행 배열  
- `pass3` (선택): `{ committed, gain, score_before, score_after, metrics }` — `metrics`에 `commit_reason`, `length_allowed`, 내부 트랜스포트 수 등이 포함될 수 있음  

Pass3 **before/after** 비교는 연속된 두 Pass3 프레임의 `mining_map` / `pass3.score_*`로 할 수 있다.

## Pass3 `_find_weighted_route_to_tree` 렉시코그래픽 키 (7튜플)

우선순위 낮을수록 좋다 (min-heap). 대략:

1. 소행성 **내부** 트랜스포트 셀 증가분  
2. 기회 점수(opportunity) 합 증가  
3. 고기회 셀 통과 횟수 등 (tier)  
4. 중기회 tier  
5. `_route_cell_cost` 누적  
6. 경로 길이  
7. 턴 수  

고정 stub·이미 `route_tree`에 포함된 셀은 비용 0.

## Pass3 셀 비용 vs Zone A–E 초안

Pass3 진입 비용은 `_route_cell_cost`가 정본이다 (외부 1, void 접경 경계 20+opportunity, mineable 120+opportunity, 그 외 암석 내부 60). 예전 문서의 Zone A–E 수치는 **튜닝 목표 후보**이며 코드와 1:1이 아니다. 변경 시 단위 테스트로 고정한다.

## `cost_grid.py` / repair 경로

`repair_cell_cost`·`find_min_demolition_path`는 **Pass3 “채굴 우선 라우팅”과 별도**로, 머지/철거/복도 예약 등 **repair 시나리오**용이다. `INTERNAL_TRANSPORT_MERGE_STEP_PENALTY`는 벨트가 암석 내부를 지날 때의 merge 페널티 힌트로 쓰인다.

## 트렁크·용량·혼선

게임 상수(예: 벨트 5760/min, 풀 클러스터 720/min)는 `shapez_asteroid/extraction/constants.py` 등과 정합 가능하나, **현재 솔버 그래프는 물리 연결·셀 점유·내부 트랜스포트 최소화 중심**이다. `_route_metrics`의 `over_capacity_segments`, `bottleneck_count` 등은 **플레이스홀더(0)** 에 가깝고, 트렁크 혼선 최적화는 미구현이다. 이후 P3로 “stub 간 병합 + 용량 위반 페널티”를 채울 때 이 필드를 실값으로 연결하면 된다.

## Extension: “직선만”이 아님

`placement.extension_positions`는 여전히 **뒤로 3칸 선형** 헬퍼다. Pass1은 선형 번들, Pass2/3 스캔은 `enumerate_extension_trees` 기반 **트리**를 사용한다.

## 관련 테스트

- `tests/unit/shapez_asteroid/test_asteroid_mining_layout.py` — 타임라인·Pass3·merge 캡  
- `tests/unit/shapez_asteroid/test_mining_layout_route_costs.py` — 비용 계층·Pass3 degraded 등  
