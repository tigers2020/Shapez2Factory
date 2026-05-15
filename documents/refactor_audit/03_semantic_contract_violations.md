# Semantic Contract Violations

## 총평

- 좋은 점:
  - `domain/enums.py`
  - `domain/trace_semantics.py`
  - `placement/placement_fsm.py`
  는 `CommitReason` / `RecoveryTrigger` / `RollbackReason` / `RejectedReason` / `PlacementCommitState` 구분을 비교적 잘 고정한다.
- 문제:
  - 실제 STEP 4/8/9 orchestration이 비어 있어서, semantic contract가 “정의만 있고 수행 계층이 없는 상태”다.
  - 일부 skeleton validation과 recovery helper는 canonical semantics를 축소해 둔 상태다.

## 위반 및 drift

| File | Contract | 관측 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | final validation은 assertion-only gate | 외부 seed가 없으면 `connectivity_ok=True`로 lenient skip | `13_step9_validation.md §15.1~§15.3` | P0 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | geometry/connectivity 전 항목 검증 | 현재는 `QUARANTINED_UNROUTED`와 단순 flood만 확인 | `13_step9_validation.md §15.1~§15.2` | P0 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/corridor_opening.py` | recovery는 STEP 8 bounded branch | `pass1_post_gate`와 `step4_recovery`가 같은 파일에서 placement rollback + trace commit을 동시 처리 | `02_pipeline_control_flow.md §4.1`, `11_step8_recovery.md` | P1 | 중간 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/step4_corridor_recovery.py` | STEP 4 routing failure recovery는 routing boundary 안에 있어야 함 | 실제 구현 소유권은 placement | `08_step4_routing.md`, `11_step8_recovery.md` | P1 | 높음 | `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/orchestration.py` | protected corridor는 hard/soft/candidate lifecycle을 가져야 함 | snapshot에는 `hard_protected_corridors`, `soft_protected_corridors`만 있고 candidate lifecycle 부재 | `12_protected_corridor.md §14.2` | P1 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/corridor.py` | recovery 결과 DTO는 trace와 분리된 algorithm 결과여야 함 | `CorridorOpeningResult`가 `trace_rows`를 직접 포함 | `03_data_schema_dto.md`, `14_step10_replay_ui.md` | P1 | 높음 | `isolate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py` | replay adapter는 output-side tooling | reader가 skeleton이라 runtime contamination은 없지만 replay contract도 미완성 | `14_step10_replay_ui.md` | P2 | 높음 | `rewrite` |

## semantic namespace 상태 판정

| Namespace | 상태 | 근거 | 감사 판정 |
|---|---|---|---|
| `CommitReason` | 양호 | `domain/enums.py`, `domain/trace_semantics.py` | early freeze 권장 |
| `RecoveryTrigger` | 양호 | commit reason과 혼용 방지 테스트 존재 | early freeze 권장 |
| `RollbackReason` | 양호 | enum 분리됨 | early freeze 권장 |
| `RejectedReason` | 양호 | enum 분리됨 | early freeze 권장 |
| `PlacementCommitState` | 양호 | `placement/placement_fsm.py`가 FSM 고정 | early freeze 권장 |
| final validation semantics | 불량 | skeleton leniency | 즉시 리팩터 대상 |
| protected corridor lifecycle | 불완전 | candidate/hard 승격 구조 미구현 | 즉시 설계 격리 필요 |

## touch 금지 영역

- 조기 단계에서 직접 변경하지 말 것
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py`

이 세 파일은 현재 semantic vocabulary의 거의 유일한 안정 지점이다.
