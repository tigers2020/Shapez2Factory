# D5-2: `apply_exception_summary_defaults` read path 감사 (코드 삭제 없음)

**성격:** 삭제 전용 회귀 리팩토링 D5의 **2차 감사** — 구현 변경 없음.  
**전제:** D5-1(`e8b385a0`)에서 [`solver_service._initial_summary_fields`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_service.py)가 이미 채우던 최상위 키 6종에 대한 중복 `setdefault`가 제거됨(문서: 기존 D5-1 보고).  
**대상 함수:** [`finalize.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py) `apply_exception_summary_defaults` (대략 L833–L1056).

---

## 1. 시드 교차 (`_initial_summary_fields` / trunk stub)

### 1.1 `_initial_summary_fields` 최상위 키

`run_id`, `return_reason`, `capacity_mode`, `trunk_load`, `existing_layout_analysis`, `before_return_validate`, `solver_state_hash`, `step_hash_step4`, `step_hash_pass3`, `step_hash_p4`.

- D5-1 이후: 위 중 **6키**는 `apply_exception_summary_defaults`에서 더 이상 `setdefault` 하지 않음(중복 제거 완료).
- 나머지(`run_id`, `return_reason`, `capacity_mode`, `trunk_load`)는 예외 직후에도 `apply`가 **다시 `setdefault` 하지 않음** — `termination` dict 등에서 `summary_fields.get("return_reason")` 형태로만 참조.

### 1.2 `trunk_load` 예외 stub

[`build_step4_trunk_load_pipeline_exception_stub`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_trunk_load.py): `step4_result_state=pipeline_exception` 등 **중첩** 필드가 `solver_summary` 최상위 키와 이름이 겹칠 수 있으나, 의미는 `trunk_load` 트리 내부에 한정된다. D5-2에서는 **최상위 `setdefault` 키**만 집계한다.

---

## 2. `setdefault` 호출 규모

| 항목 | 값 |
|------|---|
| `finalize.py` 내 부분 문자열 `summary_fields.setdefault` 출현 수(함수 본문 chunk 기준) | **191** |
| 정규식으로 추출한 **첫 인자 키 문자열** 고유 개수 | **191** (중복 키 없음) |

> 전체 키 알파벳 목록은 동일 chunk에 대해 `summary_fields\.setdefault\(\s*["']([^"']+)["']` 정규식으로 재생산하면 된다.

### 2.1 중첩·직후 보강 (최상위 `setdefault` 목록에 포함되지 않는 항목)

| 위치 | 내용 |
|------|------|
| `termination` 값 dict | `tier`, `return_reason`, `degradation_causes`, `ok` — 상위 키 이름은 `termination` 하나만 `setdefault` |
| `recovery_validation_outcome` 값 dict | `commit_reason`, `rollback_reason`, `rejected_reason`, `recovery_trigger`, `pass3_commit_subtype` |
| L1057–L1059 | `_term_exc = summary_fields.get("termination")` 후 `_term_exc.setdefault("quality_tier", …)` — **`termination` 내부** 보강 |

---

## 3. 분류 태그 정의

| 태그 | 의미 |
|------|------|
| `algorithm_contract` | Algorithm 세션 문서(`documents/Algorithm/mining_solver_cursor_sessions/`)의 요약·검증·복구 절과 직접 대응되는 관측 필드 |
| `replay_ui_required` | Replay/UI/옵티마이저가 **키 존재**를 전제로 병합·표시하는 필드 |
| `report_debug_required` | NDJSON·디버그·내부 리포트가 자주 `.get` 하는 필드(알고리즘 입력 아님) |
| `duplicated_seed` | `_initial_summary_fields` 등 상위가 **동일 최상위 키**로 이미 채움 → dedupe 후보 |
| `legacy_compat_only` | 정본에 없고, 진단 라벨·테스트 고정값에 가깝게 남은 표면 |
| `unknown_keep_for_now` | 읽기 경로가 넓거나 암묵적 의존 → 삭제 보류 |

---

## 4. prefix 그룹 요약 표 (대표 read / risk)

스캔 기준: `django_apps/`·`tests/`·`scripts/debug/`에서 문자열 키 검색 및 `views.py` copy-preview 병합 목록과 대조.

| 그룹 | 키 개수(대략) | 대표 read / write | 분류 요약 | `delete_round_risk` |
|------|----------------|-------------------|-----------|---------------------|
| `geometry_*`·`connectivity_*`·`*counts`·stub/quarantine | ~15 | `finalize.build_final_solver_output` → `final_validation`; `emit_solver_summary_once` | `algorithm_contract` + `report_debug_required` | low–med |
| `step4_*` (summary 최상위) | ~18 | `views._COPY_PREVIEW_SOLVER_SUMMARY_UI_KEYS`; `django_apps/web/.../asteroid_optimizer.html`; 다수 단위 테스트 | `replay_ui_required` + `algorithm_contract` | **med–high** (`step4_committed`는 별행) |
| `pass3_*` | ~25 | `recovery_policy`, `pass3` 파이프라인, harness 테스트 | `algorithm_contract` + `report_debug_required` | med |
| `p4_reclaim_*`·`p4_soft_replace_*` | ~60+ | `reclaim_*`, `recovery_orchestrator`, `test_reclaim_shadow` 등 | `report_debug_required` 위주 | med |
| `post_reclaim_pass3_*` | ~15 | P4 이후 Pass3, `test_pass3_transport` | `algorithm_contract` + `report_debug_required` | med |
| `recovery_*`·`max_*`·`validation_recovery_*` | ~15 | `recovery_orchestrator.enrich_solver_summary_recovery`, `recovery_policy` | `algorithm_contract` + trace | med |
| `optimization_*` | ~10 | `finalize`, `views` merge, §15.4 계열 경고 | `report_debug_required` + `replay_ui_required` | med |
| `termination`·`solver_termination`·`solver_quality_*` | 소수 | `finalize`, `solver_trace`, UI tier 표시 | `replay_ui_required` + `report_debug_required` | med |
| `mineable_*`·`excluded_by_*`·`reclaim_anchor_*`·`nearest_freed_*` | ~10 | `reclaim_shadow_scan` 등에서 쓰기, 테스트 `trace`/`ss` | `report_debug_required` | med |
| 기타 (`routing_state`, `placement_*`, `pass2_spine_*`, …) | 나머지 | `views` corridor overlay, STEP4/배치 진단 | 혼합 | med |

**`duplicated_seed` (최상위):** D5-1 이후 `apply` vs `_initial_summary_fields` **동일 최상위 키** 중복은 **남아 있지 않음** (다음 dedupe는 “다른 함수가 이미 채운 값”과의 의미 중복을 별도 정의해야 함).

---

## 5. 특수: `step4_committed`

| 항목 | 내용 |
|------|------|
| `setdefault` | `finalize.apply_exception_summary_defaults` L883 `False` |
| 위험 | [`solver_permission.pass3_permission_snapshot`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_permission.py)에서 `step4_committed: bool = True` — **요약 dict에 키가 없으면** 호출부가 기본값 `True`로 두면 Pass3 권한이 달라질 수 있음 |
| 읽기 | `views.py` UI 키 목록, `asteroid_optimizer.html`, `test_step4_merge_routing`, `test_copy_preview`, NDJSON 스크립트 등 |
| 분류 | `replay_ui_required` + `algorithm_contract`(의미) |
| risk | **high** — `setdefault` 제거는 **호출부 계약 정리 없이는 불가** |

---

## 6. 부록: `goal_cells_union_legacy` (exception summary 밖)

`solver_summary` 최상위가 아니라 **STEP4 진단 `search_stats["search_mode"]`** 등에 쓰이는 **리터럴 라벨**.

| 파일 | 역할 |
|------|------|
| [`step4_merge_routing.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py) | `search_mode` 기본 기록 |
| [`step4_route_failure_detail.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_route_failure_detail.py) | `search_stats.get("search_mode") or "goal_cells_union_legacy"` |
| [`step4_route_failure_diagnostic.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_route_failure_diagnostic.py) | 동일 폴백 |
| 테스트 | `test_step4_route_failure_detail`, `test_step4_route_failure_diagnostics`, `test_step4_local_bridge_recovery`, `test_step4_remaining_partial_failure_diagnostics` 등에서 **기대값으로 고정** |

**판정:** `legacy_compat_only`에 가깝지만 **테스트·진단 스키마에 박혀 있음** → 계획대로 **삭제 전 전역 read path 정리·스키마 합의 필요**. 이번 라운드에서는 삭제하지 않음.

---

## 7. 삭제 후보 정렬 (안전 → 위험, 요약)

1. **low (다음 구현 후보 탐색):** D5-1과 동일한 패턴 — “다른 단일 시드 함수가 **같은 최상위 키**를 항상 먼저 채움”이 **명증**되는 소그룹. 현재 chunk 기준으로는 **추가 `duplicated_seed` 최상위 키가 없음** → 다음 커밋 전에 `run_solver_timeline_pipeline` 예외 직전 `summary_fields` 상태를 한 번 더 스냅샷으로 대조하는 것이 좋다.
2. **med:** `p4_reclaim_*` 중 NDJSON만 소비·테스트만 단언하는 키 — 키별 `rg` 후 소그룹 삭제.
3. **high:** `step4_committed`, `goal_cells_union_legacy` — **별행 설계·UI/권한 합의 후**.

---

## 8. 권장 “다음 한 그룹” (구현은 별 PR)

1. **1순위(감사 기준):** `run_solver_timeline_pipeline`이 예외 전에 이미 채우는 최상위 키와 `apply_exception_summary_defaults`의 교집합을 **런타임 스냅샷 또는 정적 대조**로 한 번 더 확정한 뒤, 교집합이 생기면 D5-1과 같은 **dedupe 한 그룹**만 제거.  
2. **2순위:** `p4_soft_replace_*` 또는 `reclaim_anchor_*`처럼 **읽기처가 상대적으로 좁은** prefix를 골라 `rg`로 확인 후 한 그룹.  
3. **보류:** `step4_committed`의 `setdefault(False)` — `pass3_permission_snapshot` 기본 `True`와의 상호작용 해소 전까지 유지.

---

## 9. 검증 계획 (실제 삭제 PR 시)

- 포커스: `pytest tests/unit/shapez_asteroid/` 중 변경 모듈 관련 파일.
- 게이트: `ruff check .` → `mypy .` → `black --check .`.

**이번 D5-2 감사 패스:** 코드 변경 없음 — 문서만 갱신.

---

## 10. 부록: 전체 최상위 `setdefault` 키 (191개, 알파벳순)

```
after_internal_transport_count
after_pass2_baseline_counts
after_pass2_extractor_count
after_pass3_counts
after_transport_count
baseline_internal_transport_at_reclaim_entry
before_internal_transport_count
before_pass3_counts
before_transport_count
broken_routed_route_count
cascade_corrective_attempts
cascade_reroute_count
cascade_rollback_count
connectivity_valid
disconnected_stub_count
excluded_by_committed_placement_count
excluded_by_final_route_count
excluded_by_hard_protected_count
excluded_by_soft_protected_count
existing_layout_barrier_cell_count
existing_layout_hint_coord_count
existing_layout_source_kind
extractor_drop_count
extractor_loss_due_to_step4_rollback
final_counts
final_extractor_count
final_unfinalized_placement_count
geometry_valid
internal_quarantined_count
internal_transport_delta_vs_baseline
layout_degraded
max_total_recovery_attempts
max_validation_recovery_attempts
mineable_base_count
mineable_cur_count
missing_extractor_rotation_count
nearest_freed_cell_to_candidate_sample
net_internal_transport_saved_after_reclaim
optimization_baseline_internal_transport
optimization_baseline_internal_transport_post_step4
optimization_counterfactual_aggregation
optimization_counterfactual_failure_reason
optimization_counterfactual_internal_transport_sequential_v1
optimization_internal_transport_quality_ratio
optimization_warning_count
optimization_warnings
original_extractor_count
p4_orchestration_entry_segment
p4_reclaim_accepted_shadow_count
p4_reclaim_added_extension_cells
p4_reclaim_added_extractor_cells
p4_reclaim_added_stub_cells
p4_reclaim_best_candidate
p4_reclaim_candidate_count
p4_reclaim_final_route_cells_added
p4_reclaim_final_route_count
p4_reclaim_hard_protected_count
p4_reclaim_incremental_route_attempted
p4_reclaim_incremental_route_b2_internal_transport_added
p4_reclaim_incremental_route_cells_added
p4_reclaim_incremental_route_committed
p4_reclaim_incremental_route_path_cells
p4_reclaim_incremental_route_rollback_performed
p4_reclaim_incremental_route_rollback_reason
p4_reclaim_incremental_route_skip_reason
p4_reclaim_internal_transport_budget
p4_reclaim_internal_transport_projected_added
p4_reclaim_last_commit_route_cells
p4_reclaim_last_soft_protected_candidate_cells
p4_reclaim_loop_internal_transport_cumulative_added
p4_reclaim_loop_iterations_executed
p4_reclaim_loop_max_iterations
p4_reclaim_loop_successful_commits
p4_reclaim_loop_terminated_reason
p4_reclaim_mineable_excluded_by_route_cells
p4_reclaim_protected_corridor_source
p4_reclaim_provisional_commit_attempted
p4_reclaim_provisional_commit_committed
p4_reclaim_provisional_commit_rollback_performed
p4_reclaim_provisional_commit_rollback_reason
p4_reclaim_provisional_commit_skip_reason
p4_reclaim_rejected_shadow_count
p4_reclaim_route_zone_excluded_cumulative_count
p4_reclaim_route_zone_rebuilt
p4_reclaim_selected_candidate
p4_reclaim_selected_candidate_rank
p4_reclaim_shadow_enabled
p4_reclaim_shadow_scan_limit
p4_reclaim_shadow_skip_reason
p4_reclaim_soft_protected_candidate_cells_added
p4_reclaim_soft_protected_count
p4_reclaim_transport_total
p4_reclaim_unprotected_transport_count
p4_reclaim_zero_candidate_reasons
p4_soft_replace_attempt_count
p4_soft_replace_attempted
p4_soft_replace_commit_count
p4_soft_replace_committed
p4_soft_replace_connected
p4_soft_replace_contract
p4_soft_replace_job_count
p4_soft_replace_jobs_attempted
p4_soft_replace_new_cells
p4_soft_replace_old_cells
p4_soft_replace_rejected_reason
p4_soft_replace_rejected_reasons_by_job
p4_soft_replace_selected_job_index
pass12_mixed_surface_skipped
pass12_phase
pass12_preserve_drop_reason_counts
pass2_spine_priority_applied
pass2_spine_seed_count
pass3_attempted_commit
pass3_commit_reason
pass3_commit_subtype
pass3_committed
pass3_final_committed
pass3_gain
pass3_greedy_committed
pass3_greedy_local_replacement
pass3_internal_transport_saved
pass3_map_accepted
pass3_reclaim_projected_net_internal_saved
pass3_rejected_reason
pass3_reverted
pass3_rollback_reason
pass3_skip_reason
pass3_skipped
pass3_transport_cells_removed
pass3_transport_cells_removed_total
placement_candidate_blocked_count
placement_commit_counts
post_reclaim_pass3_after_count
post_reclaim_pass3_attempted
post_reclaim_pass3_before_count
post_reclaim_pass3_delta
post_reclaim_pass3_executed
post_reclaim_pass3_greedy_local_replacement
post_reclaim_pass3_map_accepted
post_reclaim_pass3_pass3_greedy_local_replacement
post_reclaim_pass3_pass3_reverted
post_reclaim_pass3_ran
post_reclaim_pass3_reruns_used
post_reclaim_pass3_skip_reason
post_step4_extractor_count
preserve_quality
preserve_quality_score
preserve_quality_score_version
provisional_placed_row_count
quarantined_unrouted_count
reclaim_anchor_candidate_count
reclaim_anchor_failure_samples
recovery_action_plan
recovery_bounded_loop_configured
recovery_contract_phases
recovery_merge_partial_failure
recovery_post_reclaim_pass3_connectivity_break
recovery_reclaim_incremental_failure
recovery_total_attempts_used
recovery_trigger
recovery_trigger_reason
recovery_validation_outcome
recovery_validation_recovery_eligible
removed_counts
rolled_back_placement_ids
route_loss_due_to_step4_rollback
route_revalidation_passed
routing_state
solver_quality_summary
solver_quality_tier
solver_result_tier
solver_termination
step4_committed
step4_complete_commit_success
step4_failed_route_count
step4_hard_protected_no_route_breakdown
step4_known_good_route_count
step4_no_route_exhausted_breakdown
step4_partial_failure
step4_quarantined_placement_count
step4_recovery_trigger
step4_returned_layout_source
step4_rolled_back_count
step4_rolled_back_placement_count
step4_route_count
step4_routing_failure_count
step4_skipped
termination
unfinalized_placement_count
validation_recovery_attempts_used
validation_recovery_cycles_used
```
