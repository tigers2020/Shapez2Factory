# 채굴 솔버 리플레이: 보호 코리도 델타 이벤트 MVP (v7)

## 목적

`solver_replay`의 `events`에 **보호 코리도 풀(hard / soft / candidate)** 변화를 append-only로 남겨, STEP10·CI가 시점별 델타를 소비할 수 있게 한다. Phase A 오버레이([`solver_replay_corridors.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_corridors.py))와 동일 좌표 규칙(`[x,y]`, 블루프린트 규칙상 `x != 0`)을 따른다.

## 계약 버전

- **`SOLVER_REPLAY_CONTRACT_VERSION = 7`**: 네 가지 `kind` 추가. 기존 v1–v6 의미는 유지한다.

## 이벤트 `kind` (v7)

공통: 각 이벤트는 `kind`, `phase`, `payload`를 갖는다. `payload`에는 txn 스코프용 `transaction_id`, 선택 `parent_txn_id`가 포함될 수 있다([`replay_transaction_payload`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py)).

| `kind` | 설명 | `payload` 필드 |
|--------|------|----------------|
| `corridor_added` | 명시적 풀에 좌표 편입(초기 시점 기록) | `tier`: `hard` \| `soft` \| `candidate`; `cells`: `[[x,y], ...]` (정렬: y 오름차순, 동일 y면 x 오름차순) |
| `corridor_removed` | 풀에서 좌표 제거 | `corridor_added`와 동일 형태 |
| `corridor_promoted` | 티어 상승(예: candidate → soft) | `from_tier`, `to_tier`; `cells` |
| `corridor_replaced` | 동일 정책 축에서 제거+추가(소프트 경로 교체) | `tier`(보통 `soft`); `cells_removed`, `cells_added` (v5 `route_replaced`와 동일 `[x,y]` 리스트·정렬) |

알 수 없는 `kind`는 소비 측에서 무시할 수 있다(v2 계약).

## MVP 발행 정책 (의도적으로 좁힘)

1. **`corridor_added`**: STEP4 라우팅 트랜잭션이 커밋된 뒤, `routing_state`에서 [`protected_corridors_overlay_from_routing_state`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_corridors.py)로 `hard` / `soft` / `candidate`를 구하고, **비어 있지 않은 티어당 최대 1건**을 `phase=step4`, `transaction_id` = STEP4 txn id로 append한다. Pass12 스킵·STEP4 롤백 경로에서는 발행하지 않는다.

2. **`corridor_replaced`**: P4 reclaim 트랜잭션이 커밋된 뒤, `p4_trace`에서 `p4_soft_replace_committed`가 참이고 `p4_soft_replace_old_cells` / `p4_soft_replace_new_cells`가 있으면 **최대 1건**을 `phase=p4_reclaim`, `transaction_id` = P4 txn id, `parent_txn_id` = STEP4 txn id로 append한다.

3. **`corridor_removed` / `corridor_promoted`**: 현재 메인 파이프라인에서 `routing_state`의 코리도 풀은 STEP4 이후 거의 고정이며, STEP4 산출의 `soft`와 `soft_protected_candidate_corridors`는 동일 집합을 복제하는 구간이 있어 **실제 승격/제거 시나리오가 드물다**. MVP에서는 **계약·enum·단위 테스트(샘플 payload)**만 제공하고, **프로덕션에서 0건이어도 허용**한다. 이후 풀 변경·부분 롤백 경로가 생기면 발행을 연결한다.

## UI

- 옵티마이저 템플릿의 `SOLVER_REPLAY_KNOWN_KINDS`에 위 네 `kind`를 등록해 콘솔 unknown 경고만 방지한다. 툴팁·라이프사이클 패널·`_OVERLAY_KINDS` 확장은 범위 밖이다.

## 기존 `p4_soft_replace` 이벤트와의 관계

- `p4_soft_replace` 문자열 `kind`는 기존 계약에 남아 있을 수 있다. `corridor_replaced`는 **정책 축(보호 코리도)** 델타로 명시적으로 분리한다.

## 검증

- 단위: 코리도 델타 payload 빌더(빈 셀·`x==0` 제외·티어 검증).
- 통합: `contract_version == 7`, STEP4 이후 `corridor_added` 존재(라우팅이 있는 케이스).
