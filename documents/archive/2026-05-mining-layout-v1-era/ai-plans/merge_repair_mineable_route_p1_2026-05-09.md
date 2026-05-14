# 플랜: merge repair mineable route P1 (2026-05-09)

## 목표

merge 단계에서 `find_min_demolition_path` **1차**(`allow_mineable_route=False`)가 실패하면, **2차**로만 `allow_mineable_route=True`와 **merge 전용 고비용** `mineable_route_step_cost`를 적용해 재탐색한다.

## 비용·정책

- 상수: `MERGE_REPAIR_MINEABLE_ROUTE_CELL_COST = 120` ([`solver_service.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py)).
- 비용 순서(merge repair Dijkstra): void(1) &lt; extension 철거(50) &lt; mineable 한 칸(120) &lt; extractor 철거(300) — 연장 철거가 가능하면 빈 암석 관통보다 먼저 선택되기 쉽다.
- Pass3([`pass3_transport.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3_transport.py))는 `internal_delta`·`_route_cell_cost` 등 **별도 스케일**; 숫자 동일화는 하지 않음.

## 구현 요약

1. [`cost_grid.repair_cell_cost`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/cost_grid.py): `mineable_route_step_cost: int | None` 선택 인자.
2. [`weighted_routing.find_min_demolition_path`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/weighted_routing.py): 동일 인자·trace(`enter`/`not_found`).
3. [`solver_service` merge 루프](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py): 2차 호출 + `merge_repair_mineable_retry` trace. pass2 spine의 `find_min_demolition_path` 호출은 변경 없음.

## 검증

- 단위: [`test_mining_layout_route_costs.py`](../../../tests/unit/shapez_asteroid/test_mining_layout_route_costs.py)에 `repair_cell_cost`·`find_min_demolition_path` 토이 케이스.
- `pytest` / `ruff` / `black` 해당 구간.

## 관련

- P0: [`merge_repair_not_found_recovery_2026-05-09.md`](merge_repair_not_found_recovery_2026-05-09.md)
- 리서치: [`research_merge_repair_not_found_2026-05-09.md`](../../research/research_merge_repair_not_found_2026-05-09.md)
