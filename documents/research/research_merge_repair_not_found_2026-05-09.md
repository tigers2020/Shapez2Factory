# merge repair `not_found`·정책 불일치 리서치 (2026-05-09)

## 배경

`var/mining_layout_solver_trace.ndjson` 등에서 merge 단계가 `find_merge_path` 실패 후 `find_min_demolition_path`까지 갔으나 **`repair is None`**이 되면, 솔버가 **neighbor unblock / rail relocate / owner-drop / Pass3 budget_recovery** 사다리에 올리지 않고 **`return_merge_partial_failure`**로 종료하는 사례가 확인되었다.

## 관측 (trace·코드 정합)

1. **`find_merge_path`** (`routing.py`): void 전용 BFS. `building_cells`·`asteroid_cells` 통과 불가. boxed outlet이면 `bfs_visited`가 1에 가깝게 남는 것이 정상이다.
2. **`find_min_demolition_path`** (`weighted_routing.py` + `cost_grid.repair_cell_cost`): 건물(확장/추출기)은 철거 비용으로 진입 가능하나, **`allow_mineable_route=False` 기본**이면 빈 소행성 격자(`asteroid_cells`)는 **INF**로 막힌다. Pass3 쪽 내부 transport 정책과 **강도는 다르지만 방향이 다를 수 있다**.
3. **`solver_service.build_solver_timeline` merge 루프**: `len(expanded) > MERGE_REPAIR_DEMOLITION_CELL_CAP`일 때만 budget escalation이 돌던 구조에서, **`find_min_demolition_path`가 `None`인 경우에도**(P0) 동일 escalation·Pass3 `budget_recovery`를 시도하도록 바뀌었다. P1은 그 **앞단**에서 mineable 2차 탐색을 추가한다.

## 결론 (원인 가설)

- **직접 원인(당시)**: `repair is None`을 “복구 불가”로만 보고 **즉시 partial failure**하던 제어 구조(P0에서 완화).
- **부수적 원인**: repair 탐색 실패 시 trace가 `start`만 있어 **이웃 차단 이유(건물 vs 소행성 vs bounds)**를 로그만으로 분리하기 어렵다(P0에서 neighbor 진단 보강).

## P1 (2026-05-09 구현)

- merge 루프: `find_min_demolition_path` **1차**는 `allow_mineable_route=False` 유지. **`repair is None`일 때만** 2차 호출로 `allow_mineable_route=True` + `mineable_route_step_cost=MERGE_REPAIR_MINEABLE_ROUTE_CELL_COST`(120).
- [`cost_grid.repair_cell_cost`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/cost_grid.py)에 `mineable_route_step_cost` 선택 인자로 기본 `MINEABLE_ROUTE_COST`(2)와 분리.
- Pass3([`pass3_transport`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3_transport.py))와 **숫자 동일화는 하지 않음**; void &lt; 연장 철거 &lt; mineable step &lt; 추출기 철거 순으로 merge repair가 과도하게 암석만 관통하지 않게 한다.

## P2 이후 검토

- placement 단계에서 stub escape degree 0 억제 등은 **상류 예방**으로 별도 플랜이 적합하다. 구현 요약: [`documents/ai/plans/placement_stub_escape_gate_p2_2026-05-09.md`](../ai/plans/placement_stub_escape_gate_p2_2026-05-09.md).

## 참조 코드

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py` — merge 루프 `repair is None` 분기.
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/weighted_routing.py` — Dijkstra repair.
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/cost_grid.py` — `repair_cell_cost`.
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/routing.py` — `find_merge_path`.
