# SolverMutationTransaction — 경계·스코프 플랜

**상태**: 구현 착수(최소 래퍼 + 테스트). 사람 승인 후 전면 적용 범위를 확대할 수 있다.

## 목적

Pass3·P4 reclaim·recovery·소프트 복도 치환이 겹칠 때 **부분 mutation 누수**를 줄이기 위해, mining map(및 향후 라우팅 오버레이)에 대한 **복사-기반 트랜잭션 경계**를 명시한다.

## 최소 API (1차)

| 메서드 | 의미 |
|--------|------|
| `begin()` | 트랜잭션 구간 시작(중첩 미지원). |
| `commit()` | 구간 정상 종료(내부 플래그만 정리). |
| `rollback()` | 진입 시점 `_baseline`으로 `working_map`을 되돌리고, 파이프라인에 넘길 **새 딥카피**를 반환. |
| `snapshot()` | 현재 `working_map`의 딥카피. |
| `diff_mining_maps(a, b)` | (모듈 함수) 셀 단위 차이 요약: 변경 좌표 수·역할 변경 수 등. |

## 경계 (1차 적용)

- **P4 reclaim 진입**: [`solver_service.build_solver_timeline`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py)에서 `run_p4_reclaim_loop_after_pass3` 호출 직전에 `SolverMutationTransaction(map_final)`을 생성하고, 두 번째 인자로 `txn.working_map`을 전달한다. 예외 시 `rollback()`으로 P4 이전 맵으로 복구한 뒤 예외를 재전파한다.
- **Pass12 / STEP4**: 2차로 확대. 현재는 FSM·기존 스냅샷(`reclaim_shadow_commit`, `MiningLayoutGridRollback`)과 병행한다.

## 비목표 (1차)

- 중첩 트랜잭션·세이브포인트 스택.
- `routing_state` 전체에 대한 단일 CoW(별도 P2 «공간 권위» 문서 참고).

## 검증

- 단위 테스트: `tests/unit/shapez_asteroid/test_solver_mutation_transaction.py`
- 회귀: 기존 타임라인·해시 테스트 유지.

## 참고

- P4 루프: [`reclaim_shadow_commit.run_p4_reclaim_loop_after_pass3`](django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim_shadow_commit.py)
- Pass3 스냅샷 DTO: [`dto/timeline_types.MiningLayoutGridRollback`](django_apps/shapez_asteroid/services/asteroid_mining_layout/dto/timeline_types.py)
