# Algorithm deviation deletion audit

**갱신:** 2026-05-12 (Stage 0 문서 정합)  
**성격:** 삭제 **전** 감사 **초안** — 삭제 실행 플랜이 아니다. 본 패스에서는 **코드 변경 없음** (문서만).  
**1차 권위(원문):** `documents/Algorithm/mining_solver_cursor_sessions/` — **Stage 0에서 레포 내 존재를 확인**했다([`01_canonical_doc_paths.md`](./01_canonical_doc_paths.md) 표·[`../Algorithm/mining_solver_cursor_sessions/README.md`](../Algorithm/mining_solver_cursor_sessions/README.md)). `01`…`14` 분할 정본이 있으므로, **원문 대 비교는 가능**하다. 다만 본 문서의 매트릭스 **「Algorithm requirement」 열은 아직 2차 요약·`refactory` 링크에 묶여 있으며**, 행마다 **정본 파일 + 절번호 인용으로 바꾸는 작업은 Stage 1**에서 수행한다 → 현재 Action 열의 `NEEDS_SOURCE_CHECK` 는 **「절단위 인용 대기(pending line-level citation)」** 로 읽는다.  
**2차 권위(감사·요약·임시 인용):** [`02_pipeline_recovery_control_flow.md`](./02_pipeline_recovery_control_flow.md), [`04_protected_corridor_lifecycle.md`](./04_protected_corridor_lifecycle.md), [`15_final_validation_assertion_only.md`](./15_final_validation_assertion_only.md), [`placement_fsm_drift_classification.md`](./placement_fsm_drift_classification.md), [`epic_a_mvp_exceptions.md`](./epic_a_mvp_exceptions.md), [`16_replay_trace_solver_summary_layer.md`](./16_replay_trace_solver_summary_layer.md) 등.

---

## Top-level summary (deletion policy 버킷)

| 버킷 | 요약 |
|------|------|
| **immediate_delete** | 런타임 솔버 파이프라인에서 **디스크 NDJSON / 과거 `solver_summary`를 읽어 라우팅·배치 분기**하는 경로는 발견되지 않았다. **즉시 파일 단위 삭제** 대상은 정본 원문 없이 확정하지 않음(오삭제 위험). CLI·스크립트는 `ISOLATE`로 분리 권고. |
| **replace_with_algorithm_behavior** | [`epic_a_mvp_exceptions.md`](./epic_a_mvp_exceptions.md)에 고정된 **§4.3 B-class**와 정본 표가 1:1이 될 때까지, 오케스트레이터·트리거 매핑·STEP4 재진입 정책은 **“MVP 예외”가 아니라 “정본 미정렬 구현”**으로 보면 **REPLACE** 후보다(삭제가 아닌 동작 치환·루프 추가/분기 정리). |
| **isolate_to_debug_or_report** | NDJSON·`latest.ndjson`·집계 스크립트·`solver_summary` **라인 파싱**만 하는 도구는 알고리즘 코어 밖으로 격리([`16_replay_trace_solver_summary_layer.md`](./16_replay_trace_solver_summary_layer.md) 목표와 합치). |
| **keep** | STEP9가 `mining_map`만 받는 경계, `replay_events` **emit**, Pass2가 Pass1 cheap-escape 비사용, trunk_load 관측 계약 등 **관측·UI·계약 유지**로 명시된 경로. |
| **needs_source_check** | 정본 폴더는 **확보됨**; 매트릭스 각 행을 `01`…`14` 중 해당 파일의 **절번호·문장**으로 재대조하는 **Stage 1 작업이 남음**. 특히 STEP4 재시도·§4.3.1·§14 후보/확정 분리·§9.6 merged seed. |

---

## 감사 방법

1. `refactory`·`epic_a` 문서의 drift/B 표와 코드 경로 대조.  
2. `rg` 키워드: `MVP`, `compat`, `legacy`, `fallback`, `shortcut`, `no-op`, `degraded`, `debug`, `latest.ndjson`, `solver_summary`, `replay_events`, `cheap_escape`, `pass3_recovery`, `validation_recovery`.  
3. 런타임 파이프라인: `build_solver_timeline` → `run_solver_timeline_pipeline` 입력이 `decoded`(블루프린트)인지 확인; NDJSON **읽기**는 `django_apps/.../solver` 트리 밖·`scripts/` 위주인지 확인.

---

## Deletion matrix (핵심 타깃)

표기: **Conflict** = `contradicts_algorithm` | `mvp_exception_documented` | `trace_derived_contract` | `uncertain`  
**Action** = `DELETE` | `REPLACE` | `ISOLATE` | `KEEP` | `NEEDS_SOURCE_CHECK` *(Stage 1에서 정본 절 인용 후 `NEEDS_DECISION` 등으로 세분화 가능)*

| File | Function / path | Current behavior | Original Algorithm requirement (2차 요약) | Conflict | Action | Required tests |
|------|-----------------|--------------|---------------------------------------------|----------|--------|----------------|
| `solver_pipeline/recovery_orchestrator.py` | `run_solver_timeline_pipeline` | Pass12 → STEP4 **1회** → `routing_snapshot` 고정 루프에서 Pass3→P4→finalize; 실패 시 `validation_recovery_allowed`면 `pass3_recovery_context=True`로 **동일 루프** 반복. STEP4 루프 내 비재진입. | [`02`](./02_pipeline_recovery_control_flow.md): 정본 §4.3은 STEP4 재시도·rollback 등과 **1:1 아님** 가능; B로 문서화됨. | `mvp_exception_documented` | **REPLACE** (정본 선택 시) / 그 전 **KEEP** + 문서 유지 | `test_recovery_return_paths_algorithm.py`, orchestrator 단일 STEP4·루프 상한 |
| `solver_pipeline/recovery_orchestrator.py` | `_apply_layout_preserve_hard_gate` | 비-raw 입력에서 내부 transport가 merged baseline보다 악화되면 Pass3/Validate 프레임 맵을 baseline으로 되돌리고 요약·`final_validation` 일부 필드·`replay_events`에 체크포인트 기록. | preserve-first 하드 게이트는 `constants`/문서에 존재; §4.3 표와의 정렬은 정본 절 확인 필요. | `uncertain` | **NEEDS_SOURCE_CHECK** (정본 §0.5·§11과 문장 대조) | preserve 회귀·내부 transport 비교 단위 |
| `solver/recovery_policy.py` | `validation_recovery_allowed` | `ok`·unfinalized·STEP9 hard invariant만으로 bounded 루프 허용; `missing_stub`이면 hard fail로 recovery 비허용. | [`15`](./15_final_validation_assertion_only.md)·[`epic_a`](./epic_a_mvp_exceptions.md): STEP4 비재진입·§15 경계와 정합으로 기술됨. | (낮음) | **KEEP** | `test_pr4d_algorithm_final_validation_boundary.py` |
| `solver/recovery_policy.py` | `tag_reclaim_incremental_failure_from_summary` 등 | `pass3_summary`에 이미 병합된 P4 trace 플래그를 읽어 `recovery_*`·`recovery_contract_phases`를 채움. | [`16`](./16_replay_trace_solver_summary_layer.md): 요약이 **다음 패스의 유일한 분기 입력**이 되면 계층 위반; 현재 `validation_recovery_allowed`는 해당 플래그만으로 루프를 켜지 않도록 정리됨([`02`](./02_pipeline_recovery_control_flow.md)). | `trace_derived_contract` (낮은 위험, 계약 감시) | **KEEP** + 계약 주석 유지 / 이상 시 **REPLACE** (분기 제거) | recovery summary·PR4-D |
| `pass3/pass3_transport.py` | `pass3_recovery_context` 분기 | degraded greedy·`allow_degraded_connected_commit`·내부 transport 델타 게이트 완화·`COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY`. | §11 bounded recovery와 연계된 **구현 선택**; 정본 문장 대조 필요. | `mvp_exception_documented` / `uncertain` | **NEEDS_SOURCE_CHECK** | Pass3 recovery context 단위 |
| `pass3/pass3_transport.py` | `_p3e3_validate_guarded_swap_mining_map` … `fixed_output_stubs` | 고정 stub 집합을 가드 스왑 검증에 전달. | [`13_fixed_output_stub_preservation.md`](./13_fixed_output_stub_preservation.md) 정렬 목표. | (낮음) | **KEEP** | stub 보존 회귀 |
| `step4/step4_routing_state.py` | `_routing_state_from_committed_routes` | commit 스냅샷에서 `soft_protected_candidate_corridors=[]`, confirmed·`soft_protected_corridors` 동일 풀; ELA trunk seed는 `ela_trunk_seed_candidate_corridors`만. | [`04`](./04_protected_corridor_lifecycle.md): 정본 §14.2 후보/확정 분리와 **drift**; PR4-A/C로 **문서화된 구현 상태**. | `mvp_exception_documented` | **REPLACE** (정본 A 선택 시) / **KEEP** (B 유지 시 문서만) | protected corridor·P4 소비 키 회귀 |
| `reclaim/reclaim_corridors.py` | corridor merge·`P3E3_TOUCHED_FALLBACK` | Pass3 trace·solver pool 등 출처별 merge; soft/hard 소비. | §14·P4와의 중복·출처 표는 [`04`](./04_protected_corridor_lifecycle.md) 잔여 작업. | `uncertain` | **NEEDS_SOURCE_CHECK** | `test_reclaim_shadow.py` 등 |
| `placement/pass12_merged_layout_seed.py` | `seed_pass12_scratch_from_merged_existing` | `routed_ok`인 merged seed도 **`PlacementCommitState.PROVISIONAL_PLACED`**로 기록(독스트링에 §9.6 준수 명시). | [`placement_fsm_drift_classification.md`](./placement_fsm_drift_classification.md) P2는 과거 `ROUTED_CONFIRMED` 선부여 충돌이었으나 **현 코드는 PROVISIONAL** — 정본과의 잔여 차이는 원문 필요. | `uncertain` | **NEEDS_SOURCE_CHECK** (정본 §9.6 문장 확정) | merged seed·placement FSM 테스트 |
| `placement/pass12_bundle_commit.py` | `try_commit_pass1_bundle` + `pass1_allow_cheap_escape` | Pass1만 cheap void envelope 허용; Pass2는 `try_commit_pass2_bundle`만 사용. | [`09_pass12_cheap_escape_probe_contract.md`](./09_pass12_cheap_escape_probe_contract.md) — probe가 맵에 belt/pipe로 남지 않음. | (낮음) | **KEEP** | Pass1/2 probe·commit 분리 회귀 |
| `placement/pass12_route_probe.py` | `bundle_route_probe_or_reject` | Pass2는 `pass2_no_p1_cheap_escape_envelope`; goal·cheap 진단 병합. | 정본 §9.2와의 정렬은 [`09`](./09_pass12_cheap_escape_probe_contract.md) 참조. | `uncertain` | **NEEDS_SOURCE_CHECK** | route probe 계약 테스트 |
| `step4/step4_merge_routing.py` | stub·shortcut·`goal_cells_union_legacy` | stub-in-trunk 시 Dijkstra 생략·`ROUTED_CONFIRMED` 승격; 진단에 `search_mode` legacy 문자열. | placement 표 P3·P6·[`02`](./02_pipeline_recovery_control_flow.md) 연계; legacy 라벨은 계약/진단. | `trace_derived_contract`(telemetry) | **KEEP** (라벨) / **REPLACE** (알고리즘이 금지 시 검색 모드 정리) | step4 routing·stub 회귀 |
| `solver_pipeline/finalize.py` | `layout_degraded`·`ok` vs partial success | degraded가 `solver_termination`과 결합되어 `return_reason`·trace에 반영. | §15 assertion-only와 “부분 성공”의 관계는 정본 재확인 필요. | `uncertain` | **NEEDS_SOURCE_CHECK** | 타임라인·summary 계약 테스트 |
| `solver/solver_service.py` | 예외 시 `build_step4_trunk_load_pipeline_exception_stub` | 파이프라인 예외 시 최소 summary. | 관측용 stub; 알고리즘 본경로와 분리되어야 함. | `uncertain` | **KEEP** (예외 계약) | 예외 경로 emit 테스트 |
| `solver/solver_replay_frames.py` | `build_replay_ui_frames` 등 | 타임라인→UI 프레임·이벤트 enrich. | [`16`](./16_replay_trace_solver_summary_layer.md): 알고리즘 입력 아님. | 없음 | **KEEP** | replay 프레임 단위 |
| `scripts/p4_pass3_trace_review.py` | NDJSON 마지막 `solver_summary` | 파일에서 metrics 읽어 리뷰 출력. | 알고리즘 입력 아님. | 없음 | **ISOLATE** | 스크립트 스모크(선택) |
| `scripts/aggregate_pass12_recoverability_from_ndjson.py` | NDJSON 스캔 | `solver_summary` 행 집계. | 디버그/리포트. | 없음 | **ISOLATE** | 스크립트 단위 |
| `scripts/pass12_preserve_recovery_ab.py` | trace에서 `solver_summary` 발췌 | A/B 실험·리포트. | 디버그. | 없음 | **ISOLATE** | 없음 또는 경량 |
| `django_apps/web/...` (copy-preview 등) | UI가 `solver_summary` 병합 | 표시용. | 알고리즘 결정과 분리. | 없음 | **KEEP** | UI 계약 테스트 |

---

## B-classified (§4.3) 재평가 — 정본 대비 삭제 정책

[`epic_a_mvp_exceptions.md`](./epic_a_mvp_exceptions.md) 표를 **삭제 감사 관점**에서만 재해석한다.

| Trigger (문서상) | 삭제 정책 관점 | 권고 Action |
|------------------|----------------|-------------|
| `step4_routing_failure` | “MVP 예외 보존”만으로 **코드 삭제**는 부적절 — 동작 자체가 정본 표와 어긋남. | **REPLACE** (STEP4 재시도·rollback 계약 구현) 또는 Algorithm 정본에 **명시 예외** 추가 후 **KEEP** |
| `step4_capacity_failure` | 용량 트리거·게이트 희석. | **REPLACE** (트리거·요약 분리) + **NEEDS_SOURCE_CHECK** |
| `pass3_connectivity_break` | remedial STEP4 등 세부 미정렬. | **REPLACE** (normalization) 또는 정본 완화 |
| `final_validation_failure` | STEP9-only 해석 vs Pass3→P4 루프. | **REPLACE** 또는 정본에 bounded 루프 명시 |

**요약:** B는 “당장 삭제”가 아니라 **정본 채택 시 치환 대상**으로 보는 것이 본 감사의 `deletion_policy`와 맞다. “MVP 예외 코드를 무조건 DELETE”는 정본 개정 없이는 **회귀 위험**이 크므로 **REPLACE/문서 동기**를 우선 순위에 둔다.

---

## 키워드 검색 요약

| 패턴 | 대표 위치 | 감사 결론 |
|------|-----------|-----------|
| `legacy` / `backward compat` | `finalize.py` (`step4_committed` 호환), `pass1_timeline_integration` deprecated 이름, `step4_trunk_load` edges 별칭 | 계약·호환층 → **KEEP** 또는 장기 **REPLACE**(별칭 제거는 마이그레이션) |
| `degraded` | `finalize.py` `layout_degraded`, `recovery_orchestrator` `RECOVERY_APPLIED_PASS_DEGRADED_*`, `step4_merge` `step4_degraded` | 관측·recovery 모드 → **NEEDS_SOURCE_CHECK** (§11·§15와의 관계) |
| `shortcut` | `step4_merge_routing.py` (진단적 full Dijkstra 강제) | 알고리즘 위반이 아니면 **KEEP** |
| `cheap_escape` / `pass1_allow_cheap_escape` | `pass12_bundle_commit`, `pass12_route_probe`, `route_probe` | [`09`](./09_pass12_cheap_escape_probe_contract.md) 범위 → **KEEP** |
| `latest.ndjson` / NDJSON read | `scripts/p4_pass3_trace_review.py` | 런타임 입력 아님 → **ISOLATE** |
| `solver_summary` / `replay_events` in pipeline | emit·요약 병합; `validation_recovery`는 NDJSON 미사용 | [`16`](./16_replay_trace_solver_summary_layer.md) 부합 → 핵심 **KEEP**; 플래그가 분기를 증가시키면 **REPLACE** |

---

## FSM·recovery 우회 여부

- **Pass12 → STEP4 → Pass3→P4→finalize** 순서를 `run_solver_timeline_pipeline`이 한 체인으로 묶어 **STEP4를 validation 루프에 재주입하지 않음** — FSM “우회”라기보다 **고정 스냅샷 재플레이**에 가깝다. 정본이 “매 사이클 STEP4”를 요구하면 **REPLACE** 대상.  
- **PlacementCommitState**: merged seed 경로는 코드상 **PROVISIONAL** 우선(§9.6 메모와 일치). 우회로 판정하지 않음.

---

## trace/report가 알고리즘 결정을 만드는 경로

- **직접:** 런타임에서 NDJSON 파일을 읽어 Pass3/STEP4에 주입하는 코드는 **핵심 트리에서 미발견**.  
- **간접:** `pass3_summary`에 쌓인 P4 플래그 → `tag_*` → `solver_summary`에 노출. **Bounded recovery 게이트**는 `final_validation` 중심([`02`](./02_pipeline_recovery_control_flow.md) §4.3 표 주석). → 현재는 **허용**; 향후 게이트가 trace 필드에 더 의존하면 **DELETE_OR_ISOLATE** 대상으로 재분류.

---

## Staged deletion / PR 순서 (가장 작고 안전한 단위)

1. **Stage 0 — 정본 경로·인덱스:** ~~`documents/Algorithm/mining_solver_cursor_sessions/` 확보~~ **문서 정합 완료(2026-05-12):** 레포에 `01`…`14` 존재 확인, [`01_canonical_doc_paths.md`](./01_canonical_doc_paths.md) 표 갱신, 정본 [`README.md`](../Algorithm/mining_solver_cursor_sessions/README.md) 추가. *(로컬에서 경로가 안 보이면 워크스페이스·동기화 설정을 점검.)*  
2. **Stage 1 — 삭제 감사를 정본 절 인용으로 재작성:** [`algorithm_deviation_deletion_audit.md`](./algorithm_deviation_deletion_audit.md) 매트릭스의 Algorithm requirement 열을 `mining_solver_cursor_sessions` 원문 절번호로 치환, Action 재분류. **문서만.**  
3. **Stage 1-lite (선택) — scripts 격리:** NDJSON·`solver_summary` 소비 스크립트를 `scripts/debug/` 등으로 이동 — **삭제가 아니라 격리.**  
4. **Stage 2 — 계약 정리:** `solver_summary`에서 recovery 루프에 쓰이는 키만 allowlist 문서화([`16`](./16_replay_trace_solver_summary_layer.md) 작업 항목). 코드 삭제 최소.  
5. **Stage 3 — B→REPLACE(코드):** `epic_a_mvp_exceptions` 행별로 **STEP4 재진입 / capacity 트리거 / Pass3 connectivity 세부 / validation 루프 해석** 중 하나씩 PR 분리 + 회귀 `test_recovery_return_paths_algorithm.py`·PR4-D 확장.  
6. **Stage 4 — corridor A안:** [`04`](./04_protected_corridor_lifecycle.md) 목표 A 선택 시에만 후보/확정 필드·소비자 전면 수정(대형 PR).  

**원칙:** 한 PR에 “오케스트레이터 + corridor + placement FSM”을 섞지 않는다 ([`placement_fsm_drift_classification.md`](./placement_fsm_drift_classification.md) 금지 사항과 합치).

---

## 검증 (본 패스)

- 문서만 작성; **pytest / ruff / mypy / black 미실행** (요구사항: documentation-only).
- **Stage 0(정본 경로):** `documents/Algorithm/mining_solver_cursor_sessions/` 디렉터리 존재 및 `01`…`14` 파일명 전부 존재(셸·리포 파일 트리로 확인). `rg mining_solver_cursor_sessions documents` 로 교차 확인 권장.

---

## 이후 진행 상황

1. ~~Algorithm 정본 디렉터리를 저장소에 넣은 뒤~~ **Stage 0 완료** — 다음은 **Stage 1(문서):** 매트릭스 **Algorithm requirement**·**Action** 열을 정본 **파일 + 절** 인용으로 **덮어쓰기**.  
2. `immediate_delete` 후보를 정본 대조로 **구체 파일/함수**까지 좁힌다(현재는 보수적으로 비움).  
3. Stage 1 문서 완료 후, 코드 변경은 플랜 승인 하에 Stage 2~4·[`AGENTS.md`](../../AGENTS.md) 게이트.
