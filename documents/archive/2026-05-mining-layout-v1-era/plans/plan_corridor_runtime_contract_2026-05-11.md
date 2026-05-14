# Corridor 런타임 계약 초안 (STEP4 이후)

## 배경

- **현재**: [`step4_routing_state.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py)가 커밋된 route로 **셀 단위** `hard_protected_corridors` / `soft_protected_corridors` 및 중첩 `protected_corridors`를 조립한다. P4는 [`reclaim_corridors.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py)에서 이 풀을 `ProtectedCorridorSets`(셀 frozenset)로 소비한다.
- **STEP4 관측**: [`step4_trunk_load.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_trunk_load.py)의 `transport_usage_load["trunk_edge_load"]`는 canonical undirected 키 `x1,y1--x2,y2`로 **그래프 엣지** 트래버설을 집계한다.

## 갭 (이 계약이 다루는 범위)

- 셀 풀과 엣지 부하는 **서로 다른 단위**다. 승격·원자적 교체·롤백을 “corridor 엔티티”로 맞추려면 **edge ↔ corridor_id** (또는 세그먼트 id) 매핑이 필요하다.
- Replay/UI는 [`solver_replay_corridors.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_corridors.py)의 셀 오버레이와 별도로, 엣지 heatmap을 같은 키 규칙으로 붙일 수 있다.

## 제안 스키마 (Phase A–B)

### A. edge → corridor_id

- 입력: STEP4 확정 path 집합 + `canonical_trunk_edge_key` 규칙.
- 출력: `corridor_id`는 결정적 문자열(예: 해당 컴포넌트 엣지 키 정렬 해시 또는 “stub_anchor_kind” 접두 + 순번). **동일 엣지 키는 단일 id**를 공유한다.

### B. corridor 메타데이터 (routing_state 확장 후보)

| 필드 | 의미 |
|------|------|
| `id` | corridor_id |
| `edge_keys` | `trunk_edge_load`와 동일 문자열 목록(정렬) |
| `transport_kind` | `shape_belt` \| `fluid_pipe` |
| `protected_level` | `candidate` \| `soft` \| `hard` (정책 엔진이 할당; STEP4 초기값은 soft/hard 셀 풀과 정합 필요) |
| `created_phase` | `step4` \| `pass3` \| … |
| `replacement_allowed` | bool |

### 셀 풀과의 관계 (필수 불변)

- `hard` / `soft` **셀** 집합은 기존 P4·STEP9와의 호환을 위해 유지한다.
- corridor 세그먼트의 **엣지 엔드포인트 셀** 합집합이 soft/hard와 모순되지 않도록 정의한다(하위 집합 또는 명시적 “확장 soft” 정책을 문서에 한 가지만 선택).

## Pass3·Recovery와의 정렬

- Pass3 lex 혼잡 슬롯은 **동일 canonical edge 키**로 `trunk_edge_load`에서 가중치를 조회한다.
- Recovery에서 interior 제거 시, STEP4 스냅샷상 `shared_threshold` 이상 엣지에 닿는 victim은 후순위 또는 스킵(구현 티켓에서 튜닝).

## 다음 문서 작업

- P4 DTO가 셀 전용인 한, reclaim이 엣지 단위 정책을 쓰면 **셀↔엣지 역투영** 규칙을 별도 절로 추가한다.
