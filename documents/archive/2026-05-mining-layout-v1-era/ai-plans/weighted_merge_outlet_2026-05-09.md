# outlet merge 가중 repair 플랜 (2026-05-09)

## 배경 (런타임 근거)

- `after_pass2_scan` 대비 `before_return_validate`에서 `n_buildings` 감소는 **outlet merge 단계**의 `find_min_demolition_path` → `_apply_demolition_repair_for_spine`에서 발생함 (`debug-31a146.log`, `reason=outlet_merge` 연속 기록, `after_outlet_merge_phase`에서 이미 최종 `n_buildings`와 동일).
- `find_merge_path`는 void·건물 비점유만 허용. 실패 시 repair가 **기존 내부 belt/pipe(암석 내부 트랜스포트)를 비용 0으로 통과**할 수 있어, 중앙 밀도가 높은 맵에서 **짧은 demolition 경로**가 과도하게 선택될 수 있음.
- pass3의 `_find_weighted_route_to_tree`는 `internal_delta`·`opportunity_score`로 외곽·후보 블록을 선호함. outlet merge repair는 동일 철학을 **셀 비용**에만 최소 반영함.

## 목표

1. merge repair가 **암석 내부 기존 트랜스포트**를 지날 때 void·저비용 우회(또는 덜 치밀한 구간)를 **동일 1차 목적(총 repair 비용 + extractor/extension tie-break)** 안에서 상대적으로 선호하도록 한다.
2. **게임 규칙 위반 금지**: `allow_mineable_route` 기본값 변경 없음, 암석 내부 관통 신규 허용 없음.
3. 기존 `find_merge_path` void 성공 경로는 **변경 없음**.

## 입력 고정 (구현 계약)

| 항목 | 정의 | 비고 |
|------|------|------|
| `route_tree` | merge 루프 시점의 `set[Coord]` (앵커 + 이미 연결된 belt) | `find_min_demolition_path`의 `goals` |
| `locked_cells` | `frozenset(route_tree)` | 기존과 동일 |
| `protected_cells` | 기본 `frozenset()` | 기존과 동일 |
| `asteroid_cells` | `asteroid_frozen` | repair 탐색 경계·암석 판정 |
| `buildings` | 현재 `dict[Coord, str]` | demolition 비용·종류 |
| `transport_cells` | 현재 `dict`의 key 집합 | 기존 belt 위치 |
| **내부 트랜스포트** | `frozenset({ c for c in transport_cells if c in asteroid_frozen and c not in outlet_stubs })` | `outlet_stubs = frozenset(outlets_order)` — pass3 `internal_transport_count`와 동일 조건(스텁 제외) |
| **스텝 페널티** | `INTERNAL_TRANSPORT_MERGE_STEP_PENALTY` (상수, `cost_grid.py`) | 기본 **12** — extension demolition(50)보다 작게 두어 “필요한 철거”는 유지하되 중앙 밀도 높은 통로만 상대적으로 비싸게 함 |
| `search_margin` (merge만) | `max(8, shapez_manhattan(outlet, anchor) + 24)` | spine과 유사하게 탐색 창 확대(경로 클리핑 완화) |

## 변경 파일

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/cost_grid.py` — `repair_cell_cost`에 내부 트랜스포트 스텝 가산 옵션.
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/weighted_routing.py` — `find_min_demolition_path`가 위 옵션을 `repair_cell_cost`에 전달.
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py` — outlet merge 분기에서만 `internal_transport_cells`·`search_margin`·페널티 상수 전달; **NDJSON 디버그 계측(`debug-31a146`) 제거**.

## 검증

- `python -m pytest tests/unit/shapez_asteroid/test_asteroid_mining_layout.py`
- (선택) 동일 입력으로 솔버 1회 실행 후 `n_buildings`·demolition 이벤트 수가 이전 대비 개선되는지 `_algo_dbg_append` + 타임라인 프레임으로 비교.

## 구현 상태

- **반영됨 (2026-05-09)**: `cost_grid.repair_cell_cost` 내부 트랜스포트 스텝 가산, `find_min_demolition_path` 옵션 전달, outlet merge에서만 `search_margin`·내부 belt 집합·`INTERNAL_TRANSPORT_MERGE_STEP_PENALTY` 적용. 세션 NDJSON(`debug-31a146`) 계측은 제거됨.

## 튜닝 게이트

- 상수 `INTERNAL_TRANSPORT_MERGE_STEP_PENALTY`(기본 12)·`search_margin` 오프셋(+24) 변경 시 본 플랜의 **검증 절차**를 다시 밟는다.

## 한계 (체감 없음 — 2026-05-09)

1. **1차 키는 `repair_cell_cost` 합산**이다. extension 철거 50·extractor 300이 경로를 지배하면, belt 스텝에 큰 가중을 줘도 **동일 철거 개수·동일 총액**인 후보가 나란히 남아 순위가 안 바뀐다.
2. **페널티 대상 집합**은 `mining_map`의 `asteroid_cells`(occupied+inferred) 안에 깔린 belt만 포함한다. **void 격자 위의 기존 belt**는 pass3 `internal_transport` 정의와 마찬가지로 여기서 제외되므로, “중앙이 void belt”인 맵에서는 집합이 비거나 작다.
3. belt만 비싸게 하면 어떤 후보에서는 **철거가 상대적으로 더 싸** 보이게 되어 건물 손실이 늘 수도 있다. `n_buildings` 보존이 목표면 **빈 암석 관통(`allow_mineable_route`)·merge 순서·기회비용 기반 철거비** 등 다른 축이 필요하다.
