# Replay incremental snapshot / streaming (설계 초안)

## 배경

`build_solver_timeline`은 현재 **단일 실행** 끝에 `solver_replay` 스냅샷(프레임 순서·요약 키·append-only `events`)을 반환한다. 문서상 `computation_cycle`·주기 갱신이 정의되어 있다면, UI 타임라인 스크러버·장시간 솔버 실행에서 **증분 스냅샷**이 필요해진다.

## 옵션 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **A. `events`만 확장** | 계약 단일화, 기존 `normalizeSolverReplayPayload` 패턴 재사용 | 이벤트 폭증, 대용량 map diff는 부담 |
| **B. `snapshots[]` 병렬 채널** | 주기별 전체/부분 상태를 명시적으로 분리 | 계약 버전·UI 병합 로직 추가 |
| **C. 하이브리드** | `events`는 mutation만, `snapshots[k]`는 N cycle마다 요약 해시·카운트 | 구현·테스트 분기 |

## 권장 방향 (초기)

1. **계약 v3 후보**에 `snapshots`를 **선택 필드**로 추가:  
   `{ "at_event_index": int, "step_hash": str, "summary": { ... } }`  
   전 맵 바디는 넣지 않고 해시·카운터 위주로 시작해 페이로드 폭주를 막는다.

2. **`computation_cycle`** 은 스냅샷 삽입 간격의 **논리 단위**로만 쓰고, 실제 간격은 솔버 내부 루프(P4 iteration, STEP4 trunk pass 등)에 매핑한다.

3. **UI**: `normalizeSolverReplayPayload`에서 알 수 없는 키는 무시·기본값 처리(기존 v2 방침 유지).

## 검증

- 단위 테스트: 스냅샷이 있을 때 `frame_order`·`events` 순서와 `at_event_index` 단조 관계.  
- 결정론: 스냅샷 요약은 `transaction_id` 등 비결정론 필드 제외 후 비교.

## 관련 코드·문서

- [`solver_replay_events.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_replay_events.py) — `SOLVER_REPLAY_CONTRACT_VERSION`
- [`solver_service.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py) — `build_solver_replay_snapshot`
- 웹: `django_apps/web/templates/web/asteroid_optimizer.html` — `normalizeSolverReplayPayload`
