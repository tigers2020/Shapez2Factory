# 목표: 파이프라인·Recovery 제어 흐름과 §4.3 정렬

## 배경

- 정본: `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.1–§4.3, `11_step8_recovery.md` §13.2.
- 구현: `recovery_orchestrator.run_solver_timeline_pipeline`은 Pass12 이후 STEP4를 실행하고, **`step4_routing_failure`이면 `recovery_return_policy_for_trigger`를 읽은 뒤 정책이 `reenters_step4`일 때 STEP4를 최대 1회 더 호출**한다(D2-B2-DEL; `MAX_VALIDATION_RECOVERY_ATTEMPTS`와 **별개** — 그 상수는 Pass3→P4 `for va` 루프에만 쓴다). 그 다음 **마지막 STEP4 결과**로 `routing_snapshot`을 고정하고 Pass3→P4→finalize를 돈다. `step4_recovery_trigger`가 여전히 `step4_routing_failure`이면 **검증 전용 `validation_recovery` 추가 사이클은 하지 않는다**(고정 bad snapshot 반복 제거).

## Mini-audit 산출물 (구현 전)

- **1차 표·식별자 사전·A/B 초안:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) (2026-05-12). Epic A 코드 착수 전에 표의 Expected 열을 정본 인용으로 맞출 것.

## 제어 구조(오케스트레이터 기준선)

`recovery_orchestrator.run_solver_timeline_pipeline`:

1. **Pass12** → **STEP4**(최초 1회 + `step4_routing_failure` 시 정책 기반 **최대 1회** 동일 입력 재호출)
2. **고정:** 마지막 STEP4의 `map_after_routing`으로 `routing_snapshot` 생성
3. **루프(`max_cycles`):** `routing_snapshot` 복사 → Pass3 → P4 → finalize(STEP9)
4. `out["ok"]` 이면 종료. `validation_recovery_allowed(out)`이 **아니면** 종료. **`step4_recovery_trigger == step4_routing_failure`이면** 검증 루프 추가 진입 없이 종료. 그 외에는 `pass3_recovery_context=True`로 **동일 루프** 재실행.
5. **`for va` 루프 본문 안에서는 `run_step4_stage`를 호출하지 않음**(STEP4 재시도는 루프 **앞**에서만).

## §4.3 Recovery trigger별 복귀 경로 — drift 표 (구현 매핑)

**판별 기준:** return path·rollback·`run_solver_timeline_pipeline` 루프만 본다(trace 필드명만으로 제어 의미 추론 금지). 정본 표 전문·Expected 요약은 [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.2–5.3.

| Trigger | Current code path | Algorithm return path | Drift | Change/Test |
|--------|-------------------|------------------------|-------|-------------|
| `step4_routing_failure` | STEP4 내부 + 오케스트레이터: `recovery_return_policy_for_trigger` 후 **정책 `reenters_step4`면 STEP4 최대 1회 추가**; 동일 트리거면 **검증 루프만의 추가 사이클 없음**. alternate trunk·rollback 본구현은 미완. | 표: STEP4 재시도·rollback·alternate trunk | **부분** | **D2-B2-DEL:** bad snapshot 위 validation-only 반복 제거. 잔여: alternate trunk 등. |
| `step4_capacity_failure` | 별도 canonical `recovery_trigger` 문자열 없음. 용량·cascade는 STEP4 내부(`step4_p2c_corrective` 등) `cascade_corrective_attempts`로만 관측. `validation_recovery_allowed`는 용량을 게이트에 넣지 않음. | 표: STEP4 재시도·offending rollback | **yes** | **B:** 예외·매핑 문서화. **카운터:** `cascade_corrective_attempts`(STEP4)는 `validation_recovery_attempts_used` / `recovery_total_attempts_used`(recovery 체인)와 **별도 필드** — 혼동 시 코드 수정. |
| `pass3_connectivity_break` | `pass3.py`: bridge 실패 시 `pass3_reverted`, `map_final=map_after_routing` 후 **동일 사이클**에서 P4(reclaim 경로) 진행. | 표: §4.3.1 → STEP6 Reclaim; remedial STEP4는 별도 분기 | **부분** | **B:** “STEP6 = reclaim 루프” 해석이면 근접. canonical vs `pass3_connectivity_reject_sample` 구분은 mini-audit §2. |
| `post_reclaim_pass3_connectivity_break` | `solver_timeline._run_post_reclaim_pass3_once`: 검증 실패 시 **입력 맵 return**·`post_reclaim_pass3_pass3_reverted`. `p4_reclaim.run_p4_reclaim_stage`는 해당 호출을 **한 블록에서 1회**만 수행; 동일 rerun 블록 내 재탐색 루프 없음. | 표: rollback → STEP9; 추가 rerun 없음 | **no**(STEP7 블록) | 회귀: `p4_reclaim` 소스 단일 호출·gate `post_reclaim_pass3_reruns_used`. 이후 `validation_recovery`는 **STEP9 hard invariant**(`final_validation_failure`)일 때만 별 트리거. |
| `reclaim_incremental_failure` | `p4_reclaim` 루프 내 롤백 후 지속; `tag_reclaim_incremental_failure_from_summary`. | candidate rollback 후 STEP6 계속 | **no** | 기존 `recovery_policy`·P4 테스트 유지. |
| `final_validation_failure` | `validation_recovery_allowed`가 STEP9 hard invariant만 허용([`step9_reports_hard_invariant_failure_for_bounded_recovery`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_policy.py)). 통과 시 Pass3→P4→finalize **추가 사이클**; STEP4 미재진입. | 표: recovery 후 STEP9 재검증; STEP4 자동 재실행 없음 | **no**(STEP4) / **부분**(표를 “STEP9만 재실행”으로 좁게 읽을 때) | **B:** MVP 예외 문서화. PR4-D: [`test_pr4d_algorithm_final_validation_boundary.py`](../../tests/unit/shapez_asteroid/test_pr4d_algorithm_final_validation_boundary.py), [`15_final_validation_assertion_only.md`](./15_final_validation_assertion_only.md). |

### Attempt / counter 분리 (Algorithm 불변식)

| 구분 | 필드·상수 | 역할 |
|------|-----------|------|
| 총 recovery 체인 길이 | `recovery_context_chain`, `recovery_total_attempts_used`, `MAX_TOTAL_RECOVERY_ATTEMPTS` | P4 진입 상한 등(기본 무제한 0). |
| validation recovery 루프 | `validation_recovery_cycles_used`, `MAX_VALIDATION_RECOVERY_ATTEMPTS`, `pass3_recovery_context` | 오케스트레이터 `for va in range(max_cycles)`. |
| STEP4 cascade 보정 | `cascade_corrective_attempts`(`step4_result.trunk_load` → `finalize` summary) | **별도**; `MAX_CASCADE_CORRECTIVE_ATTEMPTS` 상수는 본 저장소에 없음 — Algorithm이 별도 상한을 요구하면 `foundation/constants` 추가·검증은 후속. |

## 구현 결과 (2026-05-12, §4.3 회귀 정렬 PR)

- **문서:** 본 절 drift 표를 정본 대비 **현 상태**로 고정; A/B는 epic §5.3·[epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)와 정렬.
- **코드:** `validation_recovery_allowed`는 `ok`·unfinalized·`final_validation` hard invariant만 사용 — `recovery_post_reclaim_pass3_connectivity_break` 플래그만으로는 루프를 켜지 않음(STEP9 clean이면 종료).
- **테스트:** [`test_recovery_return_paths_algorithm.py`](../../tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py) — post-reclaim·STEP9 clean·`p4_reclaim` 단일 hook·`run_solver_timeline_pipeline` 소스 계약(정책 호출·`for va` 본문에 `run_step4_stage` 없음·routing 게이트).

## D2-A: Algorithm §4.3 return policy table (코드 계약, 2026-05-12)

- **목적:** 정본 `02_pipeline_control_flow` §4.3·§4.3.1·§4.3.2 및 `13_step9_validation` §15에 대응하는 **트리거별 복귀 정책**을 코드에 명시 테이블로 고정하고, 단위 테스트로 스냅샷한다. **`step4_routing_failure`는 오케스트레이터가 `recovery_return_policy_for_trigger`를 호출해 분기**(D2-B2-DEL). 그 외 트리거는 테이블만 유지하고 본경로 강제는 D2-C 등 후속.
- **구현:** [`django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_return_policy.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_return_policy.py) — `recovery_return_policy_for_trigger`, `RecoveryReturnPolicyId`, `RecoveryReturnPolicy` 플래그(`reenters_step4`, `allows_extra_post_reclaim_pass3_rerun`, `allows_one_time_remedial_step4` 등). 트리거 문자열 상수는 [`foundation/constants.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/foundation/constants.py).
- **연결:** `recovery_policy`·`recovery_orchestrator` 모듈 독스트링에 정책 모듈 참조만 추가. 트리거×정책 id 매핑 표는 `recovery_return_policy.py`의 `_POLICY_TABLE`과 `test_recovery_return_policy_table_matches_algorithm`가 단일 권위로 고정한다.

## D2-B1: STEP4 recovery trigger 계약 (2026-05-12)

- **범위:** §4.3 `step4_routing_failure` / `step4_capacity_failure`를 **코드에서 구분 가능한 계약**으로 정렬. **오케스트레이터 STEP4 재시도는 D2-B2-DEL에서 분리**(아래).
- **구현:** [`step4/step4_recovery_trigger.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_recovery_trigger.py) — `step4_primary_recovery_trigger_from_result`는 `Step4RoutingResult`·`trunk_load`·`routing_failures[]`만 사용(`commit_reason`·replay·NDJSON·solver_summary 입력 금지). 용량은 `trunk_load["step4_capacity_failure_signal"]`(예약 bool, merge에서 미설정) 또는 실패 행 `recovery_trigger == step4_capacity_failure`일 때만 `step4_capacity_failure`로 분류.
- **전파:** [`step4_merge_routing.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py)가 `trunk_load["step4_primary_recovery_trigger"]`를 기록; unrecoverable 실패 행에 `recovery_trigger` 추가. [`finalize.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py)가 요약 `step4_recovery_trigger` 설정(Pass3 병합 후에도 STEP4 전용).
- **테스트:** [`test_step4_recovery_trigger_contract.py`](../../tests/unit/shapez_asteroid/test_step4_recovery_trigger_contract.py). 실패 유형×트리거 표는 해당 테스트·merge 모듈 주석을 본다.

## D2-B2-DEL (상태, 2026-05-12)

- **코드:** [`recovery_orchestrator.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py) — `step4_routing_failure` → `recovery_return_policy_for_trigger`; `reenters_step4`이면 **STEP4 1회 추가** 후 snapshot·baseline 갱신. `step4_recovery_trigger`가 routing 실패로 남으면 **`validation_recovery`로 Pass3→P4만 반복하지 않음**. 보정 STEP4 상한은 **`MAX_VALIDATION_RECOVERY_ATTEMPTS`와 분리**(해당 상수는 `for va`만).
- **테스트:** `test_recovery_return_paths_algorithm.test_d2_b2_orchestrator_step4_routing_contract_in_source` + 기존 정책·P4 hook 행.

## 목표 상태

- 다음 중 하나를 **명시적으로 선택**하고 문서 또는 코드에 반영한다.
  - **A)** 구현을 정본 표에 맞춘다(복귀 지점·rollback 순서·재진입 조건).
  - **B)** 현 구현을 “MVP 단순화”로 정본에 **공식 예외**로 한 절 기술한다(표 옆 “구현 매핑” 열).

본 문서 §4.3 표는 **현재 채택: B + Info** (epic §5.3·5.4와 동일).

## 작업 항목(잔여·선택)

1. ~~트리거 목록마다 현 코드 경로 표~~ → 본 문서 §4.3 표로 반영.
2. 차이가 큰 항목: §4.3.1 세부는 **B** 유지 시 코드 변경 최소.
3. `recovery_contract_phases` / replay에 canonical trigger id를 남길지는 별 티켓.

## 검증

- 단위 테스트: `tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py` 및 기존 recovery·PR4-D 구간.
- 품질: `ruff check .`, `mypy .`, `black --check .`.

## 위험

- 제어 흐름 변경은 Pass3·P4·finalize 상호 의존이 크므로 **회귀 테스트·NDJSON 계약**을 함께 갱신해야 한다.

## 참고 코드

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py`
- `solver_pipeline/pass3.py`, `p4_reclaim.py`, `finalize.py`
- `solver/solver_timeline.py` (`_run_post_reclaim_pass3_once`)
- `step4/step4_recovery_trigger.py` (D2-B1 §4.3 트리거 분류)
- `solver/recovery_policy.py`, `solver/recovery_context.py`
