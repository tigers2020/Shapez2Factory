# Route graph authority (설계 초안)

## 목적

`route_id`, 벨트/파이프 **셀 집합**, `routing_state`(보호 회랑·stub·trunk 힌트), `Step4Route.path`가 서로 어긋나면 rollback·replay·P4 soft replace 분석 비용이 커진다. **단일 권위(authority)** 를 두되, 단계별로 “이 시점의 정본”을 명시한다.

## 현재 코드에서의 사실상 정본

| 구성요소 | 역할 | 모듈 |
|----------|------|------|
| `Step4Route` | placement별 경로(좌표 시퀀스), stub·extractor, `placement_id` | `step4_merge_routing` |
| `PlacementCommitRecord.route_id` | 커밋 시점의 논리 라벨(플레이스먼트와 연동) | placement DTO |
| `routing_state` | hard/soft protected corridors 등 **STEP4 확정 후 파생** 오버레이 | `_routing_state_from_committed_routes` 등 |
| `mining_map` 행 | 물리 셀·`role`·`placement_id` 메타 | 타임라인/검증 |

셀 “소유”는 오늘날 **암시적**이다: 경로 상의 transport 셀은 해당 placement/route 맥락에 속하지만, `route_id → frozenset[Coord]` 같은 **역인덱스**는 없다.

## 목표 상태 (점진 도입)

1. **역인덱스 (선택적 캐시)**  
   - `route_id` 또는 `placement_id` → 해당 stub~trunk 구간 transport 셀(또는 path 전체).  
   - STEP4 커밋 직후·replay `ROUTE_REPLACED` 직후에만 갱신하면 충분한 경우가 많다.

2. **불변식 (단계적 assert)**  
   - 셀 단위: `spatial_authority` 계열(이미 존재).  
   - 그래프 의미: “stub가 trunk에 도달하는가”, “protected corridor 셀이 맵의 belt와 일치하는가” 등은 **별도 함수**로 narrow하게 추가 (`assert_route_graph_matches_transport_cells` 류).

3. **Replay와의 연결**  
   - `ROUTE_REPLACED.replacements[]`는 논리 교체 기록; 장기적으로는 **같은 route_id 공간**에서 이전/이후 owned_cells를 diff할 수 있어야 한다.

## 경계 (무엇을 여기서 하지 않는가)

- **새 거대 `RouteGraph` 클래스 일괄 도입**은 플랜 승인 후 단계적 리팩터 대상이다. 본 문서는 용어·정본·확장 방향만 고정한다.
- Domain 레이어 밖(UI/Django 뷰)으로 소유 규칙을 올리지 않는다.

## 관련 코드

- [`spatial_authority.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/spatial_authority.py)
- [`step4_merge_routing.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4_merge_routing.py)
- [`solver_replay_events.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_replay_events.py)

## 후속 작업 제안

1. STEP4 커밋 지점에서 `placement_id → path` 스냅샷을 한 번에 빌드하는 순수 함수 초안.  
2. `ROUTE_REPLACED` 행과 그 스냅샷의 교차 검증 테스트(회귀).  
3. P4 soft replace 경로에 동일 스키마 확장.
