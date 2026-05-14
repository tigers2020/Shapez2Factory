# 채굴 솔버 Recovery·검증·Replay 로드맵 (2026-05-10)

정본: STEP 0~10 파이프라인, bounded recovery, replay 계약(v3+). 코드 상태 기준 타당성은 Cursor 플랜 *Mining solver recovery roadmap*과 동일하다.

Replay v7 corridor delta events completed. Next: lifecycle diff-based corridor_promoted / corridor_removed emission.

## 목표

- 채굴량 최대화·내부 transport 최소화·overlap 0·replay 가능성 유지.
- **알고리즘 확장보다** recovery 계약·validation 진입·baseline 메트릭·replay UI 계약을 먼저 고정.

## 구현 묶음 및 순서

1. **P5 Recovery 계약** (`p5-recovery-contract`): `constants` + `recovery_policy` — trigger, context chain, attempt limit, terminal reason 표준화; `pass3`·`p4_reclaim`·`finalize` 소비 경로 단일화.
2. **P5 Validation 라우터** (`p5-validation-router`): `FinalValidationReport` → bounded recovery action (geometry / connectivity / quarantine 등). **Bounded 루프는 `solver_pipeline/recovery_orchestrator.py`에 두고**, `solver_service.build_solver_timeline`은 얇은 위임으로 유지.
3. **P3 Optimization baseline** (`p3-optimization-baseline`): **Pass1·Pass2 확정 직후, STEP4 이전** 스냅샷에서 `optimization_baseline_internal_transport` 계산 → summary / replay. STEP4 직후 비교가 필요하면 **별도 optional 필드**(A/B·실험용).
4. **P3E3 기본화** (`p3e3-default-hardening`): 테스트 보강 → 소형 fixture에서 기본 True → 전역 기본값 전환.
5. **P6 Replay UI** (`p6-replay-ui-contract`): `ui_frames`·`computation_cycle`·overlay payload를 UI 1급 입력으로 승격; `contract_version` 정리.

## 병렬 작업

- `p5-validation-router`는 `p5-recovery-contract` 이후(또는 계약 필드 합의 직후) 착수.
- `p3-optimization-baseline`·`p3e3-default-hardening`: summary/trace 키만 조율되면 recovery 본구현과 **병렬** 가능.
- `p6-replay-ui-contract`: additive 계약이면 병렬 착수 가능; breaking 변경 시 다른 브랜치와 **동시 배포·버전** 조율.

## 승인·검증

- 의미 있는 동작 변경 전 사람 승인(프로젝트 게이트).
- 합류 시: `python -m pytest`, stabilization·replay·타임라인 관련 테스트 필수.

## P5 요약 계약 필드 (solver_summary / STEP9)

| 필드 / 별칭 | 의미 |
|-------------|------|
| `recovery_terminal_reason` | 문서·리뷰에서 말하는 **terminal_reason**과 동일 개념(런타임 키는 이 이름). `recovery_context.finalize_recovery_terminal_reason`이 채움. |
| `recovery_trigger_reason` | P4 진입 등 복구 트리거(§13). `pass3_summary`에서 `finalize`까지 전달. |
| `recovery_context_chain` | 복구 세그먼트 append-only 리스트. |
| `recovery_validation_outcome` | P5 롤업: `commit_reason`, `rollback_reason`, `rejected_reason`. 단계별 `pass3_*` / `p4_*` 롤백·거절 문자열은 그대로 두고, `recovery_policy.synthesize_recovery_validation_outcome`이 집계. |
| `validation_recovery_attempts_used` | bounded 검증 재시도 루프에서 사용한 **사이클 수**(1..N). `validation_recovery_cycles_used`와 **동일 값**으로 맞춤. |
| `recovery_action_plan` | `FinalValidationReport` → `recovery_orchestrator.route_validation_recovery_actions` 순서: overlap → connectivity → quarantine → geometry. 액션 id는 `foundation/constants.py`의 `RECOVERY_ACTION_*`. |
| `optimization_baseline_internal_transport` | Pass1·Pass2 확정 직후(STEP4 이전) 맵에서 계산한 내부 transport 기준치. |
| `optimization_warnings` | 기준치 대비 최종 `after_internal_transport_count` 등(현재: baseline 초과 시 `OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE`). `solver_summary`·`final_validation`·`solver_replay.optimization_metrics`에 동일 리스트 반영. |
| `solver_replay.optimization_metrics` | `baseline_snapshot_kind`(`pass1_pass2_pre_step4`), pre/post-STEP4 baseline counts, `final_internal_transport_count`, `optimization_warnings`. |
| `final_validation` (optimization) | `optimization_baseline_snapshot_kind`, `optimization_baseline_internal_transport`, post-STEP4 baseline, `optimization_final_internal_transport_count`. |

용량(capacity) 하드 실패는 STEP9 DTO에 없음 → `FinalValidationReport` 주석 및 STEP4 `trunk_load` trace만.

## 구현 메모 (코드 기준)

- **Replay v5 `transport_kind`**: `solver_replay_events.normalize_replay_transport_kind` 및 옵티마이저 템플릿 `normalizeReplayTransportKind`로 `belt`/`pipe` 별칭을 `shape_belt`/`fluid_pipe`로 통일(UI·JSON 경계).
- `MAX_TOTAL_RECOVERY_ATTEMPTS` / `MAX_VALIDATION_RECOVERY_ATTEMPTS` 기본값 **0** → 단일 정방향 파이프라인 유지; 상향 시 `recovery_orchestrator.run_solver_timeline_pipeline`의 검증 재시도 루프가 활성화된다.
- `SOLVER_REPLAY_CONTRACT_VERSION` **4**: `ui_frames`에 `primary_for_step10_ui`, `computation_cycle_ui_*`, `overlay_event_indices` 추가.
- P3E3 기본값은 하드닝 테스트(``tests/unit/shapez_asteroid/p3e3_default_true/``) 이후 **True**; 회귀 시 해당 디렉터리·``test_pass3_transport`` 타임라인 단언을 우선 확인한다.

## 참고 코드 경로

- Recovery: `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_context.py`
- 파이프라인: `solver_pipeline/pass3.py`, `p4_reclaim.py`, `finalize.py`, `step4.py`
- 검증: `validation/final_validation.py`
- Replay: `solver/solver_replay_events.py`, `solver/solver_replay_frames.py`
