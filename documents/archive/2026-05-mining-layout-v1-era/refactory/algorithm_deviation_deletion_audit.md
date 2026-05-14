# Algorithm deviation deletion audit

**갱신:** 2026-05-12 (Stage 1 감사 + D2-B2-DEL + **D2-C 정책 잔재 삭제**)  
**성격:** 삭제·치환 **전** 감사 스냅샷이며, D2-B2-DEL 등 코드 PR 시 **본 문서 표·큐를 동기**한다.  
**1차 권위:** `documents/Algorithm/mining_solver_cursor_sessions/` (`01_project_overview.md` … `14_step10_replay_ui.md`). 인덱스: [`01_canonical_doc_paths.md`](./01_canonical_doc_paths.md), [`../Algorithm/mining_solver_cursor_sessions/README.md`](../Algorithm/mining_solver_cursor_sessions/README.md).  
**2차(참고):** [`02_pipeline_recovery_control_flow.md`](./02_pipeline_recovery_control_flow.md), [`04_protected_corridor_lifecycle.md`](./04_protected_corridor_lifecycle.md), [`15_final_validation_assertion_only.md`](./15_final_validation_assertion_only.md) 등 — **Conflict·Action·Reason은 정본 문장과의 대조로만** 적는다. “B-class” 같은 refactory 전용 라벨과, **이전 감사의 ‘소스 점검 대기’ 토큰**은 쓰지 않는다.

---

## Top-level summary (Action 건수)

아래는 본 문서 **두 표**(메인 매트릭스 + §4.3 트리거 표)의 **Action 열 합계**다(메인 22행 + 트리거 **5**행).

| Action | 건수 |
|--------|-----:|
| **DELETE** | 1 |
| **REPLACE** | 3 |
| **ISOLATE** | 4 |
| **KEEP** | 15 |
| **NEEDS_DECISION** | 5 |

---

## 감사 방법

1. **정본 읽기 순서(권장):** `02_pipeline_control_flow.md`(§4 전체) → `11_step8_recovery.md`(§13) → `12_protected_corridor.md`(§14) → `08_step4_routing.md` / `09_step5_pass3_transport.md` / `10_step6_reclaim_loop.md` → `13_step9_validation.md`(§15) → `14_step10_replay_ui.md`(§16) → 나머지 `01`·`03`·`04`·`05`·`06`·`07`.  
2. **구현 경로(레포 루트 기준):** `django_apps/shapez_asteroid/services/asteroid_mining_layout/` 이하 `solver_pipeline/`·`solver/`·`pass3/`·`step4/`·`placement/`·`reclaim/` 등.  
3. **키워드 보조:** `rg`로 `fallback|legacy|compat|degraded|cheap_escape|ndjson|solver_summary|pass3_recovery` 등을 찾되, **판정은 정본 절 인용 후**에만 확정한다.

**정본 14파일 인덱스(경로 고정):**  
`documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md` · `02_pipeline_control_flow.md` · `03_data_schema_dto.md` · `04_step0_decode.md` · `05_step1_reconstruction.md` · `06_step2_pass1_placement.md` · `07_step3_pass2_placement.md` · `08_step4_routing.md` · `09_step5_pass3_transport.md` · `10_step6_reclaim_loop.md` · `11_step8_recovery.md` · `12_protected_corridor.md` · `13_step9_validation.md` · `14_step10_replay_ui.md` (공통 접두사 `documents/Algorithm/mining_solver_cursor_sessions/`).

---

## Deletion matrix (메인)

**Conflict:** `contradicts_algorithm` | `not_in_algorithm_scope` | `telemetry_or_ui_only` | `uncertain`  
**Action:** `DELETE` | `REPLACE` | `ISOLATE` | `KEEP` | `NEEDS_DECISION`

| File | Code path | Canonical Algorithm source | Conflict | Action | Reason | Test needed |
|------|-----------|---------------------------|----------|--------|--------|-------------|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py` | `run_solver_timeline_pipeline` (`step4_routing_failure` 시 `recovery_return_policy_for_trigger` + 정책 `reenters_step4`면 STEP4 **최대 1회 추가** 후 `routing_snapshot` 고정; 동일 트리거면 `validation_recovery` 추가 사이클 없음; `MAX_VALIDATION_RECOVERY_ATTEMPTS`는 `for va`만) | `02_pipeline_control_flow.md` **§4.3**·`11_step8_recovery.md` **§13.3** | uncertain | NEEDS_DECISION | `step4_routing_failure` 경로는 D2-B2-DEL로 **고정 bad snapshot 위의 검증-only 반복** 제거. §13.3과 Pass3→P4 전체 재실행 해석은 **별도 규범 확정** 필요. | `test_recovery_return_paths_algorithm.py` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py` | `_apply_layout_preserve_hard_gate` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4** STEP 목록의 STEP 0.5: 「Existing layout analysis (read-only context; 배치 변경 없음)」. `documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md` **§15.4**: counterfactual baseline·optimization 경고는 hard invariant와 분리. | uncertain | NEEDS_DECISION | 비-raw 입력에서 내부 transport가 악화되면 Pass3/Validate **타임라인 프레임**을 baseline으로 되돌림. 정본이 “타임라인 프레임 단위 복원”을 허용하는지 명시가 없어 **계약(관측 vs 본경로)** 판단 필요. | preserve·gate 회귀(기존 `_apply_layout_preserve_hard_gate` 단위) |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_policy.py` | `validation_recovery_allowed`, `step9_reports_hard_invariant_failure_for_bounded_recovery` | `documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md` **§15.3**: 「capacity overflow … Final validation에서는 새 route를 만들지 않는다」「Final validation recovery는 MAX_VALIDATION_RECOVERY_ATTEMPTS를 초과할 수 없다」. `documents/Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md` **§13.1** attempt limit. | telemetry_or_ui_only | KEEP | STEP9 hard invariant만으로 bounded 루프 허용·missing stub 시 차단 등은 §15·§13과 정합. | `test_pr4d_algorithm_final_validation_boundary.py` 등 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_policy.py` | `tag_*`, `synthesize_recovery_validation_outcome`, `append_recovery_contract_phase` | `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md` **§16.3** trace event schema(`recovery_trigger` 등). `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.2** bounded 상수·요약 필드. | telemetry_or_ui_only | KEEP | 요약·페이즈는 **다음 패스의 유일한 분기 입력**이 되면 안 되나, 현 구조는 STEP9 게이트와 병행하는 **관측·계약**에 가깝다. 이상 시 D2에서 분기 의존도만 축소. | recovery summary·PR4 계약 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_transport.py` | `pass3_recovery_context` → `allow_degraded_connected_commit`·내부 transport 델타 게이트·`COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY` | `documents/Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md` **§13.3** `validation_recovery` + `documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md` STEP 5(내부 transport 최소화) 목표. | uncertain | NEEDS_DECISION | 오케스트레이터 행과 동일 이슈: **완화된 Pass3 재실행**이 §13.3 “최소 repair”에 포함되는지 규범 확정 필요. | Pass3 recovery context 단위 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_transport.py` | `_p3e3_validate_guarded_swap_mining_map` + `fixed_output_stubs` | `documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md` **§15.1**: 「fixed output stub가 Pass3에서 제거되지 않았다」 | (없음) | KEEP | 고정 stub 보존은 hard invariant 정본과 직접 대응. | stub 보존 회귀 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py` | `_routing_state_from_committed_routes` (`ela_trunk_seed_candidate_corridors`, `soft_protected_candidate_corridors=[]`) | `documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md` **§14.2.3** `ExistingLayoutAnalysis` 힌트: `main_trunk_candidate` → `candidate_corridor` 또는 `soft_protected_candidate` — STEP 4 commit 전까지 확정 아님. **§14.2.1** candidate 생명주기. | uncertain | KEEP | ELA trunk seed를 hard와 분리 직렬화하는 것은 §14.2.3과 **방향 일치**; 소비자·해시 제외는 계약 문서화 이슈. | protected corridor·P4 소비 키 회귀 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py` | `_soft_cells_for_merged_stub_route` (stub-in-trunk soft 풀) | `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` **§9.6**: 「Stub가 이미 external trunk에 포함된 경우… **no-op route commit**… `PROVISIONAL_PLACED` → `ROUTED_CONFIRMED` 승격」 | (없음) | KEEP | 정본이 명시한 최적화(no-op commit) 경로. | step4 routing·stub 회귀 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | corridor merge·`P3E3_TOUCHED_FALLBACK` 등 | `documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md` **§14.2–§14.3** + `documents/Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md` reclaim 맥락. | uncertain | NEEDS_DECISION | 출처별 merge·fallback이 §14의 hard/soft/replacement 순서와 **완전 동치**인지는 reclaim+P4 통합 리뷰가 필요. | `test_reclaim_shadow.py` 등 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_merged_layout_seed.py` | `seed_pass12_scratch_from_merged_existing` + `PlacementCommitState.PROVISIONAL_PLACED` | `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` **§9.6**: Pass1도 Pass2와 동일하게 「routing 미확정 배치」·`PROVISIONAL_PLACED`. | (없음) | KEEP | merged seed의 provisional 기록은 정본 FSM과 합치. | merged seed·placement FSM 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_bundle_commit.py` | `try_commit_pass1_bundle` + `pass1_allow_cheap_escape` | `documents/Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md` **§7.3**: cheap escape path는 Pass2 occupied에 넣지 않음. | (없음) | KEEP | Pass1-only cheap void envelope는 정본 경계와 일치. | Pass1/2 probe·commit 분리 회귀 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py` | `bundle_route_probe_or_reject` (`pass2_no_p1_cheap_escape_envelope`) | `documents/Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md` **§7.2–§7.4** escape feasibility·probe. | (없음) | KEEP | Pass2가 Pass1 cheap envelope를 쓰지 않는 계약은 정본 “실제 route는 STEP 4”와 합치. | route probe 계약 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py` | stub-in-trunk no-op·`step4_degraded`·진단 `search_mode` 기본 `goal_cells_union_legacy` | `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` **§9.6** no-op commit·**§9.6 State authority** (`step4.degraded` 정의). `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md` **§16.3** `search.search_mode` 허용 값 목록. | telemetry_or_ui_only | KEEP | no-op·degraded는 정본에 명시. `goal_cells_union_legacy` 문자열은 스키마에 없는 관측 라벨일 수 있어 **추후** §16.3 확장 또는 REPLACE 후보이나, 알고리즘 **본경로 위반**으로 보지 않음. | step4 merge·진단 스냅샷 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py` | `layout_degraded`·`ok` vs partial success·`solver_termination` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.4** `PARTIAL_SUCCESS` / `SOLVER_FAILURE`. `documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md` **§15.4** optimization-only 실패는 solver failure 아님. | (없음) | KEEP | 등급·경고는 §4.4·§15.4와 연동 가능한 관측 계약. | 타임라인·summary 계약 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py` | `summary_fields.setdefault("step4_committed", False)` 등 backward-compatible 요약 기본값 | `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` **§9.6** `pass3_gate_source` / **`explicit_arg`** — Pass3는 `trunk_load` 추론이 아니라 명시 인자가 권위. | uncertain | REPLACE | 정본은 **추론 키 혼선**을 금지. 요약 기본값이 소비자에게 “거짓 committed”를 심으면 §9.6 위반 소지 → 별칭·기본값 축소는 **D5**에서 처리. | trunk_load·pass3 gate 통합 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_service.py` | 예외 시 `build_step4_trunk_load_pipeline_exception_stub` | `documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md` **§0** 백지 구현 전제; 정본은 예외 스텁을 두지 않으나 **관측·안전 반환**으로 범위外. | not_in_algorithm_scope | KEEP | 알고리즘 입력이 아닌 서비스 경계 예외 요약. | 예외 경로 emit 테스트 |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_frames.py` | `build_replay_ui_frames` 등 | `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md` **§16.1–§16.2** replay·스냅샷. | not_in_algorithm_scope | KEEP | UI·replay는 solver 본경로 입력이 아님. | replay 프레임 단위 |
| `scripts/debug/p4_pass3_trace_review.py` | NDJSON에서 `solver_summary` 등 읽기 | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4** 파이프라인은 `decoded`/맵 입력이 권위이며, **디스크 NDJSON을 읽어 본경로에 주입**하는 단계는 없음(도구는 범위外). | not_in_algorithm_scope | ISOLATE | D1: `scripts/debug/`에 격리 완료. | 스크립트 스모크(선택) |
| `scripts/debug/aggregate_pass12_recoverability_from_ndjson.py` | NDJSON 스캔 | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4** (위와 동일: 런타임 입력 아님). | not_in_algorithm_scope | ISOLATE | D1. | 스크립트 단위 |
| `scripts/debug/pass12_preserve_recovery_ab.py` | trace에서 `solver_summary` 발췌 | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4** (위와 동일). | not_in_algorithm_scope | ISOLATE | D1. | 없음 또는 경량 |
| `scripts/debug/extract_step4_no_route_exhausted_samples.py` | NDJSON/샘플 추출(도구) | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4** (위와 동일). | not_in_algorithm_scope | ISOLATE | D1. | 선택 |
| `django_apps/web/` (copy-preview 등) | UI가 `solver_summary` 병합 | `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md` **§16** 표시 계약. | not_in_algorithm_scope | KEEP | 알고리즘 결정과 분리된 표시층. | UI 계약 테스트 |

---

## §4.3 트리거 대비 구현 정렬 (정본 표 기준)

**정본 출처:** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3** 표(Trigger / 발생 지점 / Recovery 후 복귀 / 실패 시).

| Trigger | Canonical Algorithm source (요약) | 구현 정렬 메모 | Action |
|---------|-----------------------------------|----------------|--------|
| `step4_routing_failure` | `02_pipeline_control_flow.md` **§4.3** 표: STEP 4 route 실패 → 재시도·rollback·alternate trunk | 오케스트레이터: 정책 조회 + (정책 허용 시) STEP4 **최대 1회 추가**·snapshot 갱신; **검증-only 추가 사이클 차단**. alternate trunk·rollback 본구현은 STEP4 패키지 측 잔여. | REPLACE |
| `step4_capacity_failure` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3** 표: capacity split/additional trunk 실패 → STEP 4 재시도·trunk split 후보 변경 | (`step4_routing_failure`와 동일 계열) | REPLACE |
| `pass3_connectivity_break` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3** 표 + **§4.3.1** (정본 문서) | **코드 삭제(2026-05-12):** `RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK` 상수·`recovery_return_policy._POLICY_TABLE` 행·`ROLLBACK_PASS3_THEN_STEP6_RECLAIM` 제거. 오케스트레이터에 본경로 미배선이었던 **표-only 잔재**; 보강(replay·permission·트리거 연결)은 하지 않음. `post_reclaim_pass3_connectivity_break`는 변경 없음. | **DELETE** |
| `post_reclaim_pass3_connectivity_break` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3.2**: rerun rollback → **STEP 9**, 추가 rerun 없음 | `recovery_policy.tag_post_reclaim_pass3_connectivity_break` 등으로 플래그·트리거 기록. | KEEP |
| `reclaim_incremental_failure` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3** 표: 후보 rollback → **STEP 6** 계속 / exhausted → Final validation | `tag_reclaim_incremental_failure_from_summary`와 P4 reclaim 단계와 연결. | KEEP |
| `final_validation_failure` | `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` **§4.3** 표 + `documents/Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md` **§13.3**: recovery 후 **STEP 9 재검증**, STEP 4 자동 재진입 없음 / 최소 repair | 메인 표의 `run_solver_timeline_pipeline`·`pass3_recovery_context`와 **동일 규범 이슈**. | NEEDS_DECISION |

---

## D2-C: main-path `pass3_connectivity_break` 코드 잔재 삭제 (2026-05-12)

- **제거:** `foundation.constants`의 `RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK`, `recovery_return_policy`의 해당 `_POLICY_TABLE` 행, `RecoveryReturnPolicyId.ROLLBACK_PASS3_THEN_STEP6_RECLAIM`.
- **추가 없음:** permission 예외·`RECOVERY_BRANCH`·오케스트레이터 트리거 연결·새 상수·새 파일 없음(보강형 D2-C 시도는 **되돌림**).
- **유지:** `post_reclaim_pass3_connectivity_break` / `RECOVERY_TRIGGER_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK` 및 관련 `tag_*` 동작.
- **회귀:** `test_recovery_return_paths_algorithm.test_pass3_connectivity_break_string_not_in_return_policy_table`.

---

## Deletion queue (D1–D5)

| 큐 | 내용 | 표·심볼 참조 |
|----|------|----------------|
| **D1** | NDJSON·trace 전용 스크립트 **격리**(삭제보다 우선) | 메인 표 `scripts/debug/*.py` ISOLATE 행 4건 + [`scripts/debug/README.md`](../../scripts/debug/README.md) |
| **D2** | Recovery 제어 흐름 §4.3 정렬. **D2-A:** `recovery_return_policy` 테이블(메인 경로 `pass3_connectivity_break` **표 행 삭제**·2026-05-12). **D2-B1(완료):** `step4_recovery_trigger`·`trunk_load["step4_primary_recovery_trigger"]`·용량 신호 예약·계약 테스트. **D2-B2-DEL(완료):** routing 실패 시 정책 + STEP4 최대 1회 추가·bad snapshot 위 `validation_recovery` 반복 제거. **D2-C(삭제만):** unwired 정책·상수 제거; 예외·replay·연결 **미추가**. | §4.3 REPLACE·NEEDS_DECISION |
| **D3** | Protected corridor **생명주기**·reclaim merge가 §14·§10과 완전 동치인지 정리 | `reclaim_corridors.py` NEEDS_DECISION, `step4_routing_state.py` 소비자 정리 |
| **D4** | Placement·route **shortcut**이 정본 §7·§9.6과 어긋나면 치환 | 메인 표에서 현재는 대부분 **KEEP**(§9.6 no-op 등); 새 위반 발견 시 이 큐로 이동 |
| **D5** | Algorithm이 요구하지 않는 **legacy 호환·기본값** 제거 | `finalize.py` `setdefault("step4_committed", …)` **REPLACE** 행, `search_mode` 라벨 정합은 선택 |

---

## First deletion PR 권고

- **권장 첫 PR:** **D1** — `refactor(tools): isolate NDJSON debug scripts`  
  - 대상(완료 시 경로): `scripts/debug/p4_pass3_trace_review.py`, `scripts/debug/aggregate_pass12_recoverability_from_ndjson.py`, `scripts/debug/pass12_preserve_recovery_ab.py`, `scripts/debug/extract_step4_no_route_exhausted_samples.py` 및 [`scripts/debug/README.md`](../../scripts/debug/README.md).  
  - **런타임 솔버 비침습**, 회귀 범위 최소.  
- **두 번째 이후:** **D2** (`refactor(solver): …`)는 §4.3·§13 정합으로 **동작 변경** → `test_recovery_return_paths_algorithm.py`, PR4-D 계열을 **필수**로 확장할 것.

---

## 키워드·FSM·trace (정본 링크)

- **FSM:** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.1 다이어그램이 단일 권위; 오케스트레이터의 “고정 스냅샷 + Pass3→P4 루프”는 §4.3 `final_validation_failure`·§13과 **한 줄씩** 대조할 것.  
- **trace가 결정을 바꾸는가:** `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md` §16.3; 런타임에서 NDJSON **파일 읽기**로 Pass3/STEP4에 주입하는 경로는 메인 표 기준 **범위外**(스크립트는 ISOLATE).

---

## D2-B2-DEL: Net impact (tracked `git diff --numstat` vs `origin/master`, 2026-05-12)

| Phase | Deleted | Added | Net |
|-------|--------:|------:|----:|
| 초안(중첩 mock 중심) | ~35 | ~640 | ~+605 |
| 다이어트 후 | 61 | 210 | +149 |

제거 스캐폴딩: `test_recovery_return_paths_algorithm.py`의 다중 `patch` 블록 2건 → `test_d2_b2_orchestrator_step4_routing_contract_in_source`로 대체; `test_pr4d_…test_recovery_timeline_loop_does_not_call_step4_twice` 제거(동일 단언 중복).

## Remaining deviations

| Deviation | Action |
|-----------|--------|
| alternate trunk·placement rollback을 §4.3 표와 1:1로 구현 | 다음 PR(STEP4 패키지·오케스트레이터 확장) |
| `step4_capacity_failure` 오케스트레이터 분기 | 용량 판별 신호 구현 후 |
| §13.3 vs Pass3→P4 전체 validation recovery 루프 | NEEDS_DECISION 행·정본 규범 확정 |

---

## 검증 (본 패스)

- `rg "documents/Algorithm/mining_solver_cursor_sessions" documents/refactory/algorithm_deviation_deletion_audit.md`  
- 과거 감사용 「소스 점검 대기」 라벨(구 `NEEDS_*` 계열)은 본문에서 제거함 → 해당 문자열 **grep 0건** 목표.  
- 코드 PR(D2-B2-DEL 등) 시: `python -m pytest tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py` 등 해당 구간 필수.

---

## 이후 진행 상황

1. Stage 1 본 문서 **정본 바인딩** 완료.  
2. D1 완료 후 **D2-A**(`recovery_return_policy`)로 정책 스펙 고정 → **D2-B/C**에서 오케스트레이터·Pass3 drift 치환 → D3–D5.  
3. 코드 변경 시 [`AGENTS.md`](../../AGENTS.md) 게이트·플랜 승인 절차 준수.
