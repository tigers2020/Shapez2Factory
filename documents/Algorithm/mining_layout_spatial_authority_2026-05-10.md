# Mining layout 공간 권위 — 인벤토리 및 후보 1안

## 1. 인벤토리 (현재 공존 개념)

| 구분 | 대표 소스·모듈 | 역할 |
|------|----------------|------|
| **권위 후보(정본)** | `mining_map` 행 리스트 (`x`,`y`,`role`, …) | 블루프린트 격자에 올라간 타일 상태의 직렬화. 파이프라인 대부분의 입·출력. |
| **셀 딕셔너리 뷰** | `final_validation.cells_dict_from_mining_map` | 좌표→행 dict; 라우팅·검증의 편의 뷰. |
| **Pass12 스크래치** | `Pass12LayoutScratch` (`pass12_bundle_commit`) | `transport_cells`, `blocked_cells`, `extractor_cells` 등 배치 탐색용 집합. |
| **라우트 존** | `route_zone.route_zone_for_cell`, `RouteZone` | Pass3 lex 비용·내부/외부 판별. |
| **라우팅 작업·역할** | `routing_cells` | `collect_routing_jobs`, `want_role`, 확장/추출기 종류. |
| **보호 복도** | `reclaim_corridors`, `step4` `routing_state` | hard/soft protected, reclaim 소프트 풀. |
| **mineable / asteroid** | `routing_cells.mineable_and_asteroid_coords` | 채굴 가능·소행성 내부 좌표. |
| **Pass3 롤백 스냅샷** | `MiningLayoutGridRollback` | 그래프 스크래치 복구용(맵 리스트와 별도 층). |
| **기존 레이아웃 힌트** | `existing_layout_analysis["solver_hints"]` | trunk/cleanup 후보 → Pass12 barrier·reclaim soft 병합. |

## 2. 문제 진단

- 동일 실행 안에서 **맵 리스트**와 **스크래치 집합**·**routing_state**가 어긋나면 “한 층에서는 라우트 존재, 다른 층에서는 제거” 형태의 desync가 난다.
- P4는 `map_cur` 참조가 루프 중 **교체**될 수 있어(소프트 치환 등), 호출자가 **참조 동일성**만으로 상태를 추적하면 안 된다.

## 3. 단일 권위 후보 1안 (점진 도입)

**권위**: `mining_map` 행 리스트(정규화 좌표·정렬 키는 `solver_state_hash`와 동일 규칙을 따름).

**파생(캐시만 허용)**:

- `cells_dict_from_mining_map(mining_map)` — 파생 뷰.
- `routing_state`의 protected 리스트 — STEP4 결과로부터 파생; **검증 시점**에는 맵과 함께 해시에 포함되는 키 집합이 이미 [`solver_state_hash`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_state_hash.py)에 정의됨.

**배치 탐색 스크래치**(`Pass12LayoutScratch` 등): “초안” 층으로 두되, **번들 커밋 시점**에만 권위 맵에 반영하고, 커밋 실패 시 스냅샷으로 되돌린다(기존 FSM과 정합).

**다음 단계(별도 플랜)**: `SpatialLayoutAuthority` 같은 얇은 파사드로 “맵 + STEP4 routing_state 부분집합”을 한 객체에서 스냅샷/해시/검증 입력으로 묶는다.

## 4. 관련 구현

- [`solver_mutation_transaction.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_mutation_transaction.py) — P4 진입 맵 딥카피·롤백.
- [`solver_replay_events.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_replay_events.py) — 타임라인 `frame_order`·요약 키 결정론.
