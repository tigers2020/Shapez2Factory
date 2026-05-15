# 작업 체크리스트 (Quality gate)

작업 유형에 맞는 매뉴얼을 연 뒤, 해당 단계만 체크한다.

## Mining layout solver — `mining_solver_cursor_sessions` 정렬

정본 분할 문서: [`documents/Algorithm/mining_solver_cursor_sessions/`](../Algorithm/mining_solver_cursor_sessions/). 참고용 장문 요약(구 v1 시대, **ARCHIVED**): [`Shapez2 Asteroid Mining Solver logic.md`](../archive/2026-05-mining-layout-v1-era/algorithm-root/Shapez2%20Asteroid%20Mining%20Solver%20logic.md).

### v2 단일 권위 (범위 2, 2026-05-14)

- [x] 문서 앵커: [`current_plan.md`](current_plan.md) 목표 절에 MVP 실행 순서 + legacy preview 감사 링크
- [ ] PR-C~F: v2 STEP0→10 본 구현(현재는 STEP1 reconstruction + copy-preview 분기 일부만 진행 가능)
- [x] PR-G: `SHAPEZ_MINING_LAYOUT_ENGINE=v2` 시 `copy_preview`의 **existing_layout_analysis**를 v2 `analyze_decoded_layout` JSON으로 전환·`map_timeline`은 당분간 `blueprint_map_summary` 유지 (2026-05-14 구현)
- [x] **PR-H (2026-05-14)**: 런타임 v1 import·zip 부트스트랩·`include_solver_*` 제거; 스텁 `asteroid_mining_layout_v1_deprecated/`. 동시대 문서·플랜 묶음: [v1 문서 아카이브](../archive/2026-05-mining-layout-v1-era/README.md). (물리 대규모 리네임 단독 PR은 선택)
- Pass1 Stabilization-P1 권위: 구현·replay UI 앵커는 v2 `placement/pass1_outer.py` + `placement/bundle_candidate.py`; v1 `try_commit_pass1_bundle` / `Pass12BundleCandidate`는 **아카이브 참고만** (체크리스트·Cursor 컨텍스트 drift 방지).
- [ ] **Pass1 extension topology 정본 (2026-05-14)**: [`06_step2_pass1_placement.md`](../Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md) §7.2·§7.5·Stabilization-P1 — **straight-chain-first**(extractor **output 반대** 방향 1자 체인, 최대 3 extension); **ㅗ/ㅓ/ㅏ·3방 branching은 Pass1 기본이 아님**(fallback 또는 Pass2·후속). placement 패치 전까지 **구현이 정본과 다를 수 있음** → 코드 변경 시 정본 역주입.
- [x] v2 외부 네임스페이스: [`test_import_boundaries.py`](../../tests/unit/shapez_asteroid_v2/test_import_boundaries.py) `test_v2_tree_django_apps_imports_match_allowlist`로 `django_apps.*` 교차 import allowlist 고정 (2026-05-15)

### 공통 · 스키마

- [ ] [`01_project_overview.md`](../Algorithm/mining_solver_cursor_sessions/01_project_overview.md): §0 백지 전제, §2 목표(채굴량·extension·내부 transport·외부 연결·overlap·capacity 1차 합산·bounded recovery·replay/streaming)와 구현 정합
- [ ] [`02_pipeline_control_flow.md`](../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md): §4 STEP 0–**0.5**–10 순서, §4.1 분기, §4.2 bounded 상수, §4.3 Recovery trigger 표·§4.3.1·§4.3.2 remedial/rollback
- [ ] [`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md): TransportKind 분리, PlacementCommitState FSM, RouteZone·DTO·trace 필드와 코드 동기, **§E ExistingLayoutAnalysis·DecodedExistingLayoutContext·ExistingLayoutSolverHints**

### 파이프라인 STEP (문서 번호 = 세션 파일)

- [ ] **STEP 0** — [`04_step0_decode.md`](../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md): copy decode → blueprint 추출 → solver 입력 DTO 정규화·연동; **§5.4 STEP 0.5 Existing layout analysis**
- [ ] **STEP 1** — [`05_step1_reconstruction.md`](../Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md): shell·barrier·mineable patch·기존 belt/pipe 분리; mineable 추론은 본 단계만(재배치 중 변환 금지); **§6.4 existing layout ≠ mineable field**
- [ ] **STEP 2** — [`06_step2_pass1_placement.md`](../Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md): 외곽 우선 bundle·output stub·escape feasibility·기존 trunk 연계·cheap path ≠ occupied·**Pass1 extension 정본: output 반대 straight-chain-first(§7.2·§7.5), branching 비기본**
- [ ] **STEP 3** — [`07_step3_pass2_placement.md`](../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md): 내부 보강·blocked 집합·provisional commit·STEP 4에서 route 확정
- [ ] **STEP 4** — [`08_step4_routing.md`](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md): merge-aware·capacity-aware routing, trunk seed·goal set, **§9.2.1 ExistingLayoutAnalysis trunk seed / cleanup**, 실패 시 quarantine/recovery 연계
- [ ] **STEP 5** — [`09_step5_pass3_transport.md`](../Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md): 내부 transport 최소화·가중/사전순 routing·stub 고정·연결성 깨짐 시 rollback/§4.3.1
- [ ] **STEP 6** — [`10_step6_reclaim_loop.md`](../Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md): §12.2 gain/budget·incremental routing·내부 transport 역행 방지·zone 갱신·루프 한도
- [ ] **STEP 7** — `02` §4.3.2 + [`09_step5_pass3_transport.md`](../Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md): post-reclaim Pass3 rerun 한도·실패 시 rollback → STEP 9
- [ ] **STEP 8** — [`11_step8_recovery.md`](../Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md): 비선형 branch·trigger별 복귀(§4.3 정본)·attempt 초과 시 partial/failure
- [ ] **STEP 9** — [`13_step9_validation.md`](../Algorithm/mining_solver_cursor_sessions/13_step9_validation.md): geometry·connectivity·(후속) capacity·optimization baseline 등 assertion gate; **§15.5 existing vs final 필드 분리**
- [ ] **STEP 10** — [`14_step10_replay_ui.md`](../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md): `computation_cycle`·매 10 cycle 스트리밍·pass 스냅샷·완료 후 step replay·§16.3 trace 스키마, **§16.4 existing layout 레이어**

### 횡단 — Protected corridor

- [x] Corridor Delta Event MVP
- [ ] Protected Corridor Lifecycle Diff MVP
- [ ] [`12_protected_corridor.md`](../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md): hard/soft/candidate·승격 시점·Pass3 변경 허용·candidate exhaust trace, **§14.2.3 ExistingLayoutAnalysis 초기 보호 힌트**

### Recovery branch (§13 ↔ 코드) — 매핑 표 (2026-05-10)

[`11_step8_recovery.md`](../Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md)의 §13 trigger·context·commit_reason 정의와 현 코드의 실제 필드를 1:1로 표시한다. 「반영」=정본과 동등한 키·전이가 코드에 존재, 「부분」=일부만 구현, 「미구현」=정본 아이템 없음.

| §13 항목 (정본) | 코드 필드·심볼 | 상태 |
|------------------|------------------|------|
| `recovery_trigger` (§13.1·§13.5) | `pass3_summary["recovery_trigger_reason"]` ([`solver_pipeline/pass3.py`](../archive/2026-05-mining-layout-v1-era/README.md)·[`solver_pipeline/p4_reclaim.py`](../archive/2026-05-mining-layout-v1-era/README.md)) | 부분 — `RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM` 1종만 정의 |
| `recovery_terminal_reason` (§13.1) | [`solver/recovery_context.finalize_recovery_terminal_reason`](../archive/2026-05-mining-layout-v1-era/README.md) | 반영 — `post_reclaim_pass3_success` / `final_validation_failed_after_post_reclaim_pass3` / `p4_reclaim_loop_*` |
| trigger #1 STEP4 routing failure | (코드 trigger 문자열 미정의) → STEP4 자체 rollback·`step4_routing_failure_count`·`cascade_*` | 미구현 (recovery_trigger_reason 미반영) |
| trigger #2 STEP4 capacity | capacity는 `accumulate_only` trace만 — recovery 진입 없음 | 미구현 |
| trigger #3 Pass3 connectivity break | Pass3 자체 rollback·`pass3_rollback_reason`; recovery_trigger 미설정 | 부분 |
| trigger #4 Reclaim incremental failure | `p4_reclaim_loop_*`·`p4_reclaim_provisional_commit_*` rollback | 부분 |
| trigger #5 post-reclaim Pass3 break | `post_reclaim_pass3_pass3_reverted` → terminal `final_validation_failed_after_post_reclaim_pass3` | 반영 |
| trigger #6 Final validation fail | STEP9 실패 시 `return_reason="validation_*"`; recovery 분기 없음 | 미구현 |
| `MAX_TOTAL_RECOVERY_ATTEMPTS` (§13.1) | 코드 상수 없음 (P4·post-reclaim별 개별 한도만) | 미구현 |
| `MAX_VALIDATION_RECOVERY_ATTEMPTS` (§13.1) | 코드 상수 없음 | 미구현 |
| `MAX_CASCADE_CORRECTIVE_ATTEMPTS` (§13.3) | `cascade_corrective_attempts`/`cascade_reroute_count`/`cascade_rollback_count` ([`step4/step4_p2c_corrective.py`](../archive/2026-05-mining-layout-v1-era/README.md)) | 부분 — 카운트만 노출, 명시 상수 분리 없음 |
| `MAX_RECLAIM_ITERATIONS` (§4.2) | [`foundation/constants.MAX_RECLAIM_ITERATIONS`](../archive/2026-05-mining-layout-v1-era/README.md) `=3` | 반영 |
| `MAX_POST_RECLAIM_PASS3_RERUNS` (§4.2) | `foundation/constants.MAX_POST_RECLAIM_PASS3_RERUNS` `=1` | 반영 |
| context: `budget_recovery` | merge repair budget escalation([`merge_repair_*` 플랜](../archive/2026-05-mining-layout-v1-era/ai-plans/merge_repair_not_found_recovery_2026-05-09.md)) — 별도 필드 | 부분 |
| context: `terminal_overflow_recovery` | 미구현 | 미구현 |
| context: `merge_partial_failure` | 미구현 (감지 조건도 별도 구현 필요) | 미구현 |
| context: `cascade_corrective_recovery` | STEP4 corrective reroute 경로 존재; recovery_trigger 명시 없음 | 부분 |
| context: `validation_recovery` | 미구현 | 미구현 |
| `commit_reason` enum (§13.5) | `pass3_commit_reason`·`COMMIT_REASON_GUARDED_ATOMIC=guarded_atomic_candidate`·greedy `normal_gain`·`degraded_connected_recovery` | 반영 (정본 enum 외 `guarded_atomic_candidate` 추가) |
| `recovery_context_chain` (§13) | `pass3_summary["recovery_context_chain"]` + [`extend_recovery_chain`](../archive/2026-05-mining-layout-v1-era/README.md); 세그먼트: `p4_reclaim`/`soft_replace_v2`/`post_reclaim_pass3` | 반영 |

### 세션 대조 진척 요약 (2026-05-10 · `asteroid_mining_layout` 코드베이스)

워크스페이스 기준 패키지가 **`foundation/` · `placement/` · `routing/` · `step4/` · `pass3/` · `reclaim/` · `solver/` · `solver_pipeline/` · `validation/` · `existing_layout/` · `dto/`** 등으로 모듈화되어 있으며, 공개 진입점은 [`solver/solver_service.build_solver_timeline`](../archive/2026-05-mining-layout-v1-era/README.md)이다.

| 세션·STEP | 구현 근거(요지) | 문서 대비 남은 갭 |
|-----------|------------------|-------------------|
| `02` §4 순서 | `solver_pipeline.pass12` → `step4` → `pass3` → `p4_reclaim` → `finalize` | §4.1 분기 전부를 트리거별로 문서와 1:1 매핑한 적 없음 |
| STEP 0.5 / `03` §E | [`existing_layout_analysis.analyze_existing_layout_from_mining_map`](../archive/2026-05-mining-layout-v1-era/README.md) — `solver_hints`(trunk_seed / cleanup), issues, transport 블록 | §E 필드·이름 **전 항목** 정적 대조 미실시 |
| STEP 2–3 | [`placement/pass1_timeline_integration`](../archive/2026-05-mining-layout-v1-era/README.md)·Pass12 bundle commit | `pass2_spine.spine_seed_voids_adjacent_extensions`는 **여전히 패키지 내 미참조** |
| STEP 4 | [`solver_pipeline/step4`](../archive/2026-05-mining-layout-v1-era/README.md)·`step4/` | ELA trunk를 STEP4 goal/seed로 **직접** 소비하는지 문서 §9.2.1과 별도 확인 필요 |
| STEP 5 | `pass3/pass3_transport` 등 | rollback·§4.3.1 세부는 부분 구현 가능 |
| STEP 6 | [`reclaim/reclaim_shadow_commit_loop.run_p4_reclaim_loop_after_pass3`](../archive/2026-05-mining-layout-v1-era/README.md), [`foundation/constants`](../archive/2026-05-mining-layout-v1-era/README.md) `MAX_RECLAIM_*` | 문서 상수(2 vs 3 등)와 숫자 정합은 별도 |
| STEP 7 | [`solver_timeline._run_post_reclaim_pass3_once`](../archive/2026-05-mining-layout-v1-era/README.md), [`solver_permission.post_reclaim_pass3_gate`](../archive/2026-05-mining-layout-v1-era/README.md) | rerun 한도·실패 시 STEP9 직행 등 세부 트리거 표 대조 미완 |
| STEP 8 | [`solver/recovery_context`](../archive/2026-05-mining-layout-v1-era/README.md), P4 단계의 trigger 요약 필드 | `11_step8_recovery.md` 전 트리거·복귀점 표 미대조 |
| STEP 9 | [`validation/final_validation`](../archive/2026-05-mining-layout-v1-era/README.md) | capacity·§15.5 existing vs final 분리 등 후속 항목 |
| STEP 10 | replay v3·`computation_cycle` (기존 체크리스트 기록과 동일) | §16 스트리밍·레이어 UI 정본과 별도 QA |
| Protected / ELA 힌트 | [`pass12_existing_layout_hints`](../archive/2026-05-mining-layout-v1-era/README.md), [`reclaim_corridors` solver_hints → soft](../archive/2026-05-mining-layout-v1-era/README.md) | §14.2.3·Pass3 hard 정책 전면 |

### 2026-05-10 Serena·정적 스캔 — `asteroid_mining_layout` ↔ 본 절

Serena MCP(`user-serena`) `initial_instructions` 후, 심볼·패턴 도구로 코드 확인하고 본 체크리스트만 갱신함 (구현 변경 없음).

- [x] **`find_referencing_symbols`**: `solver_service.build_solver_timeline` — 참조: [`asteroid_mining_layout/__init__.py`](../archive/2026-05-mining-layout-v1-era/README.md)·[`placement/pass1_timeline_integration.py`](../archive/2026-05-mining-layout-v1-era/README.md) docstring·[`solver/mining_layout_solver_state.py`](../archive/2026-05-mining-layout-v1-era/README.md) docstring·`tests/unit/shapez_asteroid/` 다수. `django_apps/**/*.py`에서 `**/test*.py` 제외 시 **호출부는 패키지 내부·테스트만** (뷰 등 외부 직접 호출 미검출).
- [x] **`find_referencing_symbols`**: [`placement/pass2_spine.spine_seed_voids_adjacent_extensions`](../archive/2026-05-mining-layout-v1-era/README.md) — **참조 0건** → 아래「Pass2 spine 미배선」과 정합.
- [x] **(당시 스캔 한계 — 2026-05-10b에서 정정)** `ExistingLayoutAnalysis` 문자열 검색만으로는 놓침. **현재**: [`existing_layout/existing_layout_analysis.py`](../archive/2026-05-mining-layout-v1-era/README.md)에 분석·`solver_hints` 출력·`solver_service`에서 Pass12/P4로 전달.
- [x] **(당시 스캔 한계 — 2026-05-10b에서 정정)** `MAX_RECLAIM` 등 미검출은 패턴/경로 한계. **현재**: [`foundation/constants.py`](../archive/2026-05-mining-layout-v1-era/README.md) `MAX_RECLAIM_*`, [`reclaim_shadow_commit_loop`](../archive/2026-05-mining-layout-v1-era/README.md), `post_reclaim_pass3_*` 필드·게이트([`solver_timeline`](../archive/2026-05-mining-layout-v1-era/README.md)·[`solver_permission`](../archive/2026-05-mining-layout-v1-era/README.md)) 존재.
- [x] **replay 스냅샷 v3 (코드)**: `SOLVER_REPLAY_CONTRACT_VERSION` 3 — `build_solver_replay_snapshot`가 이벤트·상위에 `computation_cycle`; Pass3는 `transaction_begin`+`pass3_layout_snapshot`(before/after)+`map_diff_committed` 또는 `rollback`로 동일 `transaction_id`.
- [x] **B1 `ui_frames` + copy-preview `solver_timeline`**: `build_replay_ui_frames`로 타임라인별 이벤트 슬라이스·Pass3 스냅샷 메타; 옵티마이저 HTML은 `map_timeline`+`solver_timeline` 연속 스크럽.
- [x] **`find_symbol`**: [`routing/route_zone.TransportKind`](../archive/2026-05-mining-layout-v1-era/README.md)·[`placement/placement_commit.PlacementCommitState`](../archive/2026-05-mining-layout-v1-era/README.md) 존재 — [`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) 일부와 코드 동기 **부분 확인**. **§E**: dict 기반 ELA + `solver_hints`는 코드에 있음(TypedDict·문서 전 필드 대조는 선택).
- [x] **영향 구간 `pytest` (본일)**: `test_pass1_timeline_integration`·`test_pass3_transport`·`test_step4_merge_routing`·`test_mining_solver_stabilization`·`test_lexicographic_router`·`test_mining_layout_route_costs` — **64 passed, 1 skipped** (`ruff`/`mypy`/`black` 전역 게이트는 본 갱신에서 미실행).

### 검증 (렉스 · 세션과 병행)

- [ ] 영향 구간 `python -m pytest` → `ruff check .` → (전역 변경 시) `mypy .` → `black .` 또는 `black --check .` — [`manuals/testing.md`](manuals/testing.md)
- [x] **2026-05-10 (세션·체크리스트 갱신)**: `python -m pytest tests/unit/shapez_asteroid/` → **293 passed, 1 skipped** (문서만 수정·`ruff`/`mypy`/`black` 전역은 미실행)
- [x] **2026-05-10 (Phase A·B 회귀)**: `python -m pytest tests/unit/shapez_asteroid/` → **297 passed, 1 skipped**. 변경 파일에 `ruff`·`mypy`·`black --check` 모두 clean. Phase A: P4·post_reclaim·recovery 필드 일관성 단언 1건 추가([`test_mining_solver_stabilization.py`](../../tests/unit/shapez_asteroid/test_mining_solver_stabilization.py) `test_build_solver_timeline_summary_p4_and_recovery_fields_consistent`). Phase B: Pass2 spine 시드 카운트 관측만 추가(동작 변경 없음, [`test_pass1_timeline_integration.py`](../../tests/unit/shapez_asteroid/test_pass1_timeline_integration.py) 회귀 3건).
- [x] **2026-05-10 (wave 종료 — Solver Architecture Reviewer 판정)**: `mining_solver_next_wave_317aa1eb.plan.md` Phase A/B/C 모두 정본과 정합으로 **종료 처리**. 다음 wave 1순위는 **「Pass2 spine ON/OFF A/B 활용 플랜」**(시드 관측 → 후보 정렬·우선순위 활용 단계). 2순위 Recovery trigger 확장(§13.5 enum), 3순위 §E TypedDict 고정.
- [x] **2026-05-10 (Pass2 spine soft 우선순위 A/B wave 완료)**: [`plans/pass2_spine_soft_priority_ab_2026-05-10.md`](../archive/2026-05-mining-layout-v1-era/ai-plans/pass2_spine_soft_priority_ab_2026-05-10.md) 정본 등록. `mineable_inner_first_order(..., priority_seeds=...)` / `run_pass2_internal_placement_mvp(..., priority_seeds=...)` / `integrate_pass12_placement_into_working_map(..., pass2_spine_priority_enabled=False)` 인자 + `solver_summary["pass2_spine_priority_applied"]: bool` 노출(기본 OFF). 솔버 외부 호출은 always-OFF, ON 분기는 단위 테스트만. 회귀: `python -m pytest tests/unit/shapez_asteroid/` → **302 passed, 1 skipped**, 변경 5파일에 `ruff`/`mypy`/`black --check` clean. 다음 1순위는 §13.5 Recovery trigger 확장.

### 2026-05-10 Asteroid solver 계약 보존 리팩터 1차

- [x] 작업 유형: `solver` / `refactor`
- [x] 범위: [`solver/solver_service.build_solver_timeline`](../archive/2026-05-mining-layout-v1-era/README.md) 오케스트레이션 유지, 내부 단계만 `solver_pipeline/`로 분리
- [x] 계약 보존: replay v2 event/transaction 필드, timeline frame id, `routing_state` hard/soft/nested protected corridor shape, Pass1→Pass2→STEP4→Pass3→P4→validate 순서 변경 없음
- [x] 회귀 보강: `solver_summary["routing_state"]` protected corridor shape end-to-end 테스트 추가
- [x] 검증: `python -m pytest tests/unit/shapez_asteroid/` → **291 passed, 1 skipped**; `python -m pytest tests/integration/web/test_web_smoke.py tests/unit/shapez_asteroid/test_copy_preview.py` → **29 passed**; `ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout tests/unit/shapez_asteroid`; `mypy django_apps/shapez_asteroid/services/asteroid_mining_layout`; `black --check django_apps/shapez_asteroid/services/asteroid_mining_layout tests/unit/shapez_asteroid`
- [x] **2차**: [`step4_merge_routing.py`](../archive/2026-05-mining-layout-v1-era/README.md)에서 STEP4 result DTO를 `step4_contracts.py`, protected corridor `routing_state` 조립을 `step4_routing_state.py`로 분리. `_dijkstra_route`·`_p2c_revalidate_and_correct` patch 지점과 `Step4Route`/`Step4RoutingResult` import 호환 유지. 검증: `test_step4_merge_routing.py` 영향 구간 → **18 passed, 1 skipped**, 전체 `tests/unit/shapez_asteroid/` → **291 passed, 1 skipped**, `ruff`, `mypy`, `black --check`.

### 2026-05-10 P0.5 Decoded existing layout (문서·계약)

- [x] 플랜: [`../plans/decoded_existing_layout_model.md`](../plans/decoded_existing_layout_model.md) — 세션 문서 접목·구현 범위 요약 **문서 존재·본문 확인**(구현은 플랜대로 별도 커밋)
- [x] **dto-contract (코어)**: [`existing_layout_analysis.py`](../archive/2026-05-mining-layout-v1-era/README.md)가 `source_kind`·`transport`·`issues`·`solver_hints` 등 §E 성격 필드를 출력·`build_solver_timeline`에서 Pass12/P4에 전달. **남음**: [`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) §E와 **필드별 1:1** 대조·(선택) TypedDict 고정.
- [x] **solver-hints-contract (배선)**: `solver_hints` → Pass2 barrier meta [`pass12_existing_layout_hints`](../archive/2026-05-mining-layout-v1-era/README.md), P4 reclaim **soft** 병합 [`reclaim_corridors`](../archive/2026-05-mining-layout-v1-era/README.md). **남음**: Pass3 **hard** trunk 보호·STEP4가 ELA trunk를 라우팅 seed/goal로 **직접** 쓰는지 등 ([`08_step4_routing.md`](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) §9.2.1, [`12_protected_corridor.md`](../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md) §14.2.3) 정본 대조.

---

### 2026-05-09 Mining layout solver stabilization (정본 플랜)

- 상세 QA·트레이스 항목: [`var/checklist.md`](../../var/checklist.md) (§0.1~§11, 부록 A)
- [ ] 작업 유형: `solver`
- [ ] 문서: [`plans/mining_layout_solver_stabilization_2026-05-09.md`](../archive/2026-05-mining-layout-v1-era/ai-plans/mining_layout_solver_stabilization_2026-05-09.md), [`current_plan.md`](current_plan.md)
- [x] **Stabilization-P0 (일부 완료)**: `emit_solver_summary_once`·`build_solver_timeline` 종료 요약(`solver_summary`)·`after_pass2` baseline proxy·[`final_validation`](../archive/2026-05-mining-layout-v1-era/README.md) geometry/connectivity 하드 게이트·용량은 `accumulate_only` trace만
- [x] **Stabilization-P1 — route probe 헬퍼**: [`bundle_route_probe_or_reject`](../archive/2026-05-mining-layout-v1-era/README.md)·`bundle_reject_no_route`
- [x] **Stabilization-P1 — 공식 Pass1/Pass2 커밋 게이트**: [`pass12_bundle_commit`](../archive/2026-05-mining-layout-v1-era/README.md) (`try_commit_pass1_bundle` / `try_commit_pass2_bundle`)·실패 시 transport/blocked 무잔류·`bundle_reject_invalid_stub`(`stub_cell`이 합쳐진 transport에 없을 때)
- [x] **Canonical P1-A — Pass1 outer-first MVP 생성기**: [`pass1_outer_placement`](../archive/2026-05-mining-layout-v1-era/README.md) (`run_pass1_outer_placement_mvp`)·커밋은 전부 `try_commit_pass1_bundle`
- [x] **Canonical P1-B — extension topology**: [`extension_topology.enumerate_extension_topologies`](../archive/2026-05-mining-layout-v1-era/README.md)·Pass1 번들 후보와 연동
- [x] **P1-C — 출력 방향·출구 스텁·cheap escape 정합**: `extractor_output_dir`·`final_validation`·cheap void 마진(동적 3~7)·Pass2는 cheap 미사용
- [x] **Pass2-A — 내부 채움 MVP**: [`pass2_internal_placement`](../archive/2026-05-mining-layout-v1-era/README.md)·inner-first·`try_commit_pass2_bundle`만·`pass2_*` 통계
- [ ] **Stabilization-P1 — 미래 배선 (나머지 생성기)**: Pass2 spine·reclaim 등은 동일하게 공식 게이트만 경유·`scratch` 직접 갱신 금지
- [ ] **미완 (안정화 플랜 나머지)**: 철거 기반 merge repair 커밋 차단·destructive 이벤트 카운트·생산 점수 검증 등
- [ ] **2차**: 배치기에서 stub→trunk probe 호출·protected corridor 최소
- [ ] **3차**: Pass3 transport-only contract·score 확장·commit 조건
- [ ] **4차**: transport graph validation·회귀 테스트(P7)
- [ ] 검증: 영향 구간 `pytest`, `ruff` / (전체 변경 시 `mypy`, `black --check`)

### 2026-05-09 Merge repair `not_found` escalation

- [x] 작업 유형: `solver`
- [x] 문서: [`research_merge_repair_not_found_2026-05-09.md`](../archive/2026-05-mining-layout-v1-era/research/research_merge_repair_not_found_2026-05-09.md), [`plans/merge_repair_not_found_recovery_2026-05-09.md`](../archive/2026-05-mining-layout-v1-era/ai-plans/merge_repair_not_found_recovery_2026-05-09.md), [`current_plan.md`](current_plan.md) 갱신
- [x] `repair is None` 시 merge budget escalation(1~4) + Pass3 `budget_recovery` 후 재시도; give-up 시 명시적 partial failure 메시지
- [x] `find_min_demolition_path` `not_found` trace에 `explored_cells`·`bounds`·`neighbor_costs` 등 진단 필드 추가
- [x] 검증: `pytest` 해당 unit 구간, `ruff` 변경 파일

### 2026-05-09 Merge repair mineable route P1

- [x] 작업 유형: `solver`
- [x] 문서: [`merge_repair_mineable_route_p1_2026-05-09.md`](../archive/2026-05-mining-layout-v1-era/ai-plans/merge_repair_mineable_route_p1_2026-05-09.md), [`research_merge_repair_not_found_2026-05-09.md`](../archive/2026-05-mining-layout-v1-era/research/research_merge_repair_not_found_2026-05-09.md) P1·관측 갱신
- [x] `cost_grid.repair_cell_cost`에 `mineable_route_step_cost`; `weighted_routing`·merge 2차 호출·`MERGE_REPAIR_MINEABLE_ROUTE_CELL_COST`
- [x] 검증: `pytest` `test_mining_layout_route_costs`, `ruff`, `black --check`

## 공통

- [x] [`AGENTS.md`](../../AGENTS.md) Manual Routing으로 매뉴얼 선택함
- [x] (해당 없음) 외부 라이브러리 문서는 Context7 MCP: `resolve-library-id` → `query-docs`, 질문당 도구 3회 상한, 쿼리에 비밀 미포함 — 이번 작업에서 신규 외부 라이브러리 문서 조회 불필요
- [x] 변경 대상 파일·호출부 확인
- [x] 의미 있는 변경이면 리서치·플랜·승인 게이트 충족 (해당 시)
- [x] 변경 파일 목록과 이유 정리
- [x] 검증 실행 또는 미실행 사유·위험 기록

### 2026-05-06 리팩터링 우선순위 문서

- [x] 작업 유형: `refactor`
- [x] 읽은 매뉴얼: [`manuals/refactor.md`](manuals/refactor.md), [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc)
- [x] 작성 문서: [`plan_refactor_priorities_2026-05-06.md`](plan_refactor_priorities_2026-05-06.md)
- [x] 코드 변경 없음. 검증은 정적 스캔(`rg`, 파일 크기 확인, import 방향 확인)으로 제한.

## 코드 품질 (로컬)

- [x] `python -m pytest` (또는 영향 구간)
- [x] `ruff check .`
- [x] `mypy .`
- [x] `black .` 또는 CI에서는 `black --check .`

### 2026-05-07 Asteroid routing barrier fix

- [x] 작업 유형: `solver`
- [x] 읽은 매뉴얼: [`manuals/solver.md`](manuals/solver.md), [`manuals/testing.md`](manuals/testing.md)
- [x] DTO 의미: `blueprint_occupied_cells`와 `transport_hard_block_cells` 분리
- [x] 라우팅 의미: routed transport를 hard block이 아닌 soft trunk로 변경
- [x] placement/reachability: cheap BFS hard block 의미를 A*와 정렬
- [x] Shapez2-MIP-Miner 참조: Gurobi 없이 route-aware coverage/saturation score 반영
- [x] 문서: occupancy gate 플랜 및 리서치 메모 갱신

### 2026-05-07 Asteroid extraction multi-pass solve

- [x] 작업 유형: `django` / 솔버 파이프라인
- [x] `EXTRACTION_MULTI_PASS_MAX`, 패스마다 `beam_place_clusters` + mineable/hard_block 누적
- [x] UI: dock `pass`, copy-preview 도움말, job `partial`에 pass 메트릭 병합
- [x] 검증: `pytest tests/unit/shapez_asteroid/`, `ruff check` (변경 파일), `black` (테스트 1파일 포맷)

### 2026-05-07 Pipe routing preferences (mineable soft + score)

- [x] `PIPE_ASTAR_MINEABLE_STEP_PENALTY`, `PIPE_ROUTE_AWARE_MINEABLE_CELL_PENALTY`, pipe A* `mineable_soft`, `_route_aware_score` pipe 분기
- [x] 검증: `pytest tests/unit/shapez_asteroid/`, `ruff check` (변경 파일)

### 2026-05-07 Multi-pass mineable vs route cells + overlay

- [x] `mineable_cur`: `hard_cur`에 합류한 경로 셀도 제외 (이전 패스 파이프 위 코어 방지)
- [x] UI: `routeByCoord`가 설비 좌표를 덮어쓰지 않음, SVG 폴리라인을 설비 셀에서 분절
- [x] 검증: `pytest tests/unit/shapez_asteroid/test_extraction_multipass.py`, `ruff` (변경 파일)

### 2026-05-07 Pipe network vs hard block (fluid trunk merge)

- [x] `solver_pipe_network_cells` + 멀티패스: 파이프 경로는 `transport_hard_block`에 넣지 않고 mineable·goal 시드만; 벨트(shape)는 기존처럼 경로를 hard에 포함
- [x] `_route_pipe_extractor_outputs` 초기 `pipe_network`에 누적 솔버 파이프 시드
- [x] 검증: `pytest tests/unit/shapez_asteroid/`, `ruff` (변경 파일)

### 2026-05-07 Fluid multipass beam: merge escape + shape hard block

- [x] `cheap_transport_escape_exists`(pipe): `solver_pipe_network_cells` 도달 = 탈출로 인정 → 2패스 이상 빔이 코어 후보를 잃지 않게
- [x] `fluid_rec`: shape 배치 좌표를 `transport_hard_block`에 합류 (파이프/저가 BFS가 shape 칸을 통과하지 않음)
- [x] 검증: `pytest tests/unit/shapez_asteroid/`, `ruff`

### 2026-05-08 2-pass repair solver 기반 작업

- [x] 작업 유형: `solver` / `refactor`
- [x] 문서: `documents/plans/plan_asteroid_mining_layout_solver_inputs_2026-05-08.md`에 extension 트리·55/71 조합·맵 검증·repair 비용/트리거 추가
- [x] 1차 scan은 기존 선형 1+3 배치로 복구하고, tree 열거/검증은 2차 전용 경로로 분리
- [x] repair용 비용 모델과 Dijkstra 기반 `find_min_demolition_path` 추가
- [x] extension parent 포인터와 서브트리 demolition 확장 추가
- [x] 순서 고정: 1차 scan → 중심부 2차 scan → 전체 outlet 파이프/벨트 merge → validate

### 2026-05-10 P4 reclaim loop + §14.3 soft corridor (코드 반영)

- [x] `run_p4_reclaim_loop_after_pass3`: shadow → provisional → P4-B2 incremental route → bounded iteration
- [x] provisional soft reject 시 `p4_reclaim_soft_corridor_transport_collision_cells` 노출 (`placed ∩ soft` 중 belt/pipe)
- [x] §14.3 `_try_atomic_replace_soft_corridor` 루프 연동·실패 시 기존 reject 유지·성공 시 `map_cur` 갱신 후 재스캔
- [x] 요약: `P4_SOFT_REPLACE_V1_CONTRACT`, `p4_soft_replace_*`(last), `p4_soft_replace_attempt_count` / `commit_count`(누적); `solver_service` `setdefault`
- [x] 검증: `pytest tests/unit/shapez_asteroid/` (242 passed, 1 skipped 세션 기준), `reclaim_shadow`·`solver_service` 대상 `mypy`

### 2026-05-10 §14.3 soft replace v2 (코드 반영)

- [x] `P4_SOFT_REPLACE_V2_CONTRACT`: 전체 routing jobs를 deterministic order로 순회
- [x] 각 job마다 replacement route probe, 첫 valid replacement만 atomic commit
- [x] 전부 실패하면 기존 reject 유지·원본 map 보존
- [x] trace: `p4_soft_replace_job_count`, `p4_soft_replace_jobs_attempted`, `p4_soft_replace_selected_job_index`, `p4_soft_replace_rejected_reasons_by_job`
- [x] summary 의미 고정: `p4_soft_replace_attempt_count` = soft replace session count, `p4_soft_replace_jobs_attempted` = last session 내부 routing job probe count
- [x] 단위: `test_soft_replace_v2_tries_multiple_jobs_until_one_succeeds`, `test_soft_replace_v2_preserves_map_when_all_jobs_fail`, `test_soft_replace_v2_records_selected_job_index`
- [x] 검증: `python -m pytest tests/unit/shapez_asteroid/` (248 passed, 1 skipped), `ruff check .`, `mypy .`, `black --check .`

### 2026-05-10 P4 soft repair UI/summary last vs count (코드 반영)

- [x] summary 한 줄에서 soft repair session 누적(`attempt_count`/`commit_count`)과 마지막 session job trace(`selected_job_index`/`job_count`/`jobs_attempted`) 분리 표시
- [x] map overlay에 마지막 soft repair old/new cells outline 추가
- [x] 예외 summary 기본값에 v2 job trace 필드 `setdefault`

### 2026-05-10 Step4 protected corridor pool (코드 반영)

- [x] Step4 route commit 결과에서 `routing_state.protected_corridors` 생성: output stub·route 끝점은 hard, 나머지 committed route path는 soft confirmed/candidate
- [x] `solver_routing_state_for_p4_reclaim` → `protected_corridors_for_reclaim` 경로가 Step4 solver pool을 우선 수신
- [x] 단위: `test_step4_committed_routes_populate_soft_protected_corridor_pool`, `test_step4_output_stub_cells_populate_hard_protected_corridor_pool`, `test_p4_reclaim_receives_step4_protected_corridor_pool`
- [x] 검증: `python -m pytest tests/unit/shapez_asteroid/` (245 passed, 1 skipped), `mypy .`, `black --check .`

## 보안·비밀

- [x] 비밀값·토큰 코드 미삽입 (품질 게이트·로케일·테스트 정리만; 비밀·프로덕션 토큰 미삽입)

자세한 명령 표는 [`manuals/testing.md`](manuals/testing.md)를 본다.
### 2026-05-08 Pass3 mining-priority transport reconstruction

- [x] 작업 유형: `solver`
- [x] `pass2 -> merge` 이후 snapshot 기준 pass3 candidate를 별도 생성
- [x] extractor output stub 1칸을 fixed로 보존하고 나머지 transport를 재라우팅 후보로 분리
- [x] 내부 mineable/extractor 후보 셀의 route cost를 높인 weighted routing 추가
- [x] candidate score gain, route length ratio, connectivity를 비교해 이득이 있을 때만 commit
- [x] pass3 timeline frame과 metric을 API 결과에 포함
- [x] 단위 테스트: stub 보존, 내부 transport 감소, pass3 frame 순서 검증

### 2026-05-09 리포 품질 게이트·로케일

- [x] `tests/unit/shapez_asteroid/test_health.py` → `test_asteroid_api_health.py` (pytest 수집 `test_health` 충돌 제거)
- [x] `ruff` E501(`pattern_catalog_repository`), `black`(`reachability`), `mypy`(placement / solver_service / 관련 테스트)
- [x] `solver_service` 번들 방향 키: B023 회피를 위해 `_tree_bundle_dir_rank_key` + `partial`
- [x] `scripts/build_locale_ko.py` KO dict: `summary must be an object` 등 4 msgid — `django.po` 재생성, `test_build_locale_ko_strict` 통과
- [x] 전역: `pytest` / `ruff check .` / `mypy .` / `black --check .`

### P2-0 — Pass12 STEP4 이전 계약 (mixed surface·요약 훅)

- [x] Pass1-only 타임라인 프레임(`solver_pass1_outer`)과 Pass2 결과(`solver_pass2_internal`) 분리
- [x] `integrate_pass12_placement_into_working_map()` 반환: `(after_pass1, after_pass2, stats)`
- [x] 호환용 `integrate_pass1_outer_into_working_map`는 Pass12 전체 후 **post-Pass2** 맵·통계 반환(문서화)
- [x] shape/fluid `surface` 혼합 맵은 Pass12 MVP 스킵(전역 dominant 병합 방지)
- [x] `solver_summary`: `pass12_phase` — `post_pass2_mvp` / `skipped_mixed_surface_mvp` / 예외 시 `exception`
- [x] non-skip Pass12 통계에도 `pass12_skipped=False`, `pass12_skip_reason=None`, `pass12_mixed_surface_skipped=False` 명시
- [x] `solver_timeline` 각 프레임 `summary`에 `pass12_phase`·`pass12_skipped`·`pass12_skip_reason` 포함(UI/replay frame-only 읽기 대비)
- [x] STEP4·Pass3 없음: `after_pass2_baseline_counts == final_counts`(코드 주석으로 계약 고정; STEP4-A에서 재분리 예정)

### P2-A — STEP4 최소 merge-aware routing (아키텍처 검토 마감 2026-05-09)

- [x] 구현·연동: [`step4_merge_routing.run_step4_merge_aware_routing`](../archive/2026-05-mining-layout-v1-era/README.md)·[`solver_service`](../archive/2026-05-mining-layout-v1-era/README.md) 호출
- [x] 단위: [`tests/unit/shapez_asteroid/test_step4_merge_routing.py`](../../tests/unit/shapez_asteroid/test_step4_merge_routing.py)
- [x] 검증: `pytest` 141 passed, 1 skipped; `ruff` 통과(기존 실패 `I001` import 정렬 — 기능 결함 아님)
- [x] 상태: **DONE** — 다음: **P2-B — `PlacementCommitState` FSM** ([`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) 정본과 코드 동기)

### P2-B — PlacementCommitState FSM (계약·검증 정합 2026-05-10)

- [x] Enum·레코드·`make_placement_id` — [`placement_commit.py`](../archive/2026-05-mining-layout-v1-era/README.md); Pass12 커밋 시 `PROVISIONAL_PLACED` — [`pass12_bundle_commit`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] 맵 행 `placement_id`·STEP4 `ROUTED_CONFIRMED` / 격실패 `QUARANTINED_UNROUTED`→`ROLLED_BACK`·rollback — [`step4_merge_routing`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] `routing_failures` 항목: `extractor_id`·`attempt_count`·`final_state`·`last_error`(및 기존 좌표 필드)
- [x] `solver_summary`·`solver_step4_routing` summary: `placement_commit_counts`·`step4_*_count` — [`solver_service`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] `final_validation`: `placement_state` 또는 `placement_commit_state`가 `quarantined_unrouted`이면 `geometry_valid=False`
- [x] 단위: [`test_step4_merge_routing.py`](../../tests/unit/shapez_asteroid/test_step4_merge_routing.py) 보강

### P2-B.1 — FSM guard·맵 메타 (2026-05-10)

- [x] `unfinalized_placement_count`(`provisional_placed`+`quarantined_unrouted`) — `trunk_load`·`solver_summary`·`solver_step4_routing`·`final_validation` API
- [x] 잔존 시 `return_reason`=`validation_unfinalized_placement_failed`·`ok`=False — [`solver_service`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] `final_validation`: 맵 행 `provisional_placed` → `provisional_placed_row_count`·geometry 실패 — [`final_validation.py`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] STEP4 후 `placement_id` 행에 `placement_commit_state`·`route_id`·`rollback_reason` 스탬프; Pass12 출력 리스트 **별도 dict 복사** 후 라우팅(타임라인 프레임 무결)
- [x] `unfinalized_placement_count_from_counts` — [`placement_commit.py`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] 단위: orphan `placement_records`·`build_solver_timeline` 패치 검증
- [x] polish (아키텍처 검토 마감): `layout_degraded`에 `step4_rollback_count`·`solver_summary` 상위 `step4_rolled_back_count`·예외 경로 `setdefault`

### P2-C — rollback cascade route revalidation (STEP4 안정화 · MVP 2026-05-10)

**제외(P2-C에서 하지 않음)**: Pass3 연결·reclaim loop·full recovery branch·capacity overflow hard constraint·`solve_result_grade`·복잡한 multi-trunk 최적화.

**핵심 검증 시나리오**: rollback된 placement가 다른 `ROUTED_CONFIRMED` route의 trunk 연결을 끊었을 때 감지 후 reroute 또는 cascade rollback으로 정리 가능한가.

- [x] rollback 이후 transport **external reachability** 재계산 (`_stub_reaches_external_trunk` / `transport_cells_reaching_external`)
- [x] `ROUTED_CONFIRMED` route별 stub 연결성 재검사
- [x] `broken_routed_route_count` 산출
- [x] broken route에 대해 **local corrective reroute** 시도 (`_dijkstra_route` 재실행·경로 반영)
- [x] 성공 시 `Step4Route` 경로 교체·기존 `route-{placement_id}` 유지
- [x] 실패 시 해당 placement **cascade rollback** (`rollback_reason`=`p2c_trunk_disconnect`)
- [x] `cascade_corrective_attempts` 한도 (`_MAX_P2C_CORRECTIVE_ATTEMPTS` = 64)
- [x] [`solver_service`](../archive/2026-05-mining-layout-v1-era/README.md) `solver_summary`·`solver_step4_routing`: `route_revalidation_passed`, `broken_routed_route_count`, `cascade_corrective_attempts`, `cascade_reroute_count`, `cascade_rollback_count`, `trunk_load`에 `cascade_rolled_back_placement_ids`
- [x] `layout_degraded`: `broken_routed_route_count` / `cascade_rollback_count` 반영
- [x] 구현 축: [`step4_merge_routing.py`](../archive/2026-05-mining-layout-v1-era/README.md) (`_p2c_revalidate_and_correct`) · `final_validation` 추가 필드 없음 · `solver_service` 요약/프레임 전파
- [x] 단위: `_stub_reaches_external_trunk` flaky 패치로 corrective reroute 경로 검증
- [x] **P2-C.1 (DONE)** 실맵 회귀: [`test_step4_cascade_revalidates_route_after_neighbor_rollback`](../../tests/unit/shapez_asteroid/test_step4_merge_routing.py) — **손 구성 `mining_map`**(y=10 단일 복도·파이프 우회 차단)·B routing 실패→stub `(15,10)` rollback으로 A 단절→P2-C가 broken 감지 후 corrective reroute/cascade·`final_validation` 통과. B만 `force_route_attempt_placement_ids`(stub-in-trunk merge 우회; 안 하면 패치가 호출되지 않음).

### P3-A — Pass3 STEP4 이후 연동 (greedy MVP · 2026-05-10)

- [x] STEP4 검증 통과 후 `run_pass3_transport_minimization_from_maps` 시도·`validate_final_mining_layout(map_try)` 게이트·실패 시 STEP4 맵 유지
- [x] `solver_timeline` `solver_pass3_transport` 프레임·`solver_summary`에 Pass3 필드 병합

### P3-B — Pass3 commit safety (void jump 제거 · 2026-05-10)

- [x] `transport_connects_outlets_to_anchor`: cardinal **동일 타일 transport** 인접만 (void 직선 점프 제거)
- [x] `reconstruct_mining_priority_transport`: 실패 시 `rejected_reason` (성공만 `commit_reason`)
- [x] `run_pass3`: `transport_kinds` 2종 이상 → `pass3_skip_reason=mixed_transport_kind_mvp`
- [x] `solver_service`: `pass3_reverted` 시 `pass3_rollback_reason`·before/after counts 요약
- [x] 단위: [`test_pass3_transport.py`](../../tests/unit/shapez_asteroid/test_pass3_transport.py)·[`test_mining_layout_route_costs.py`](../../tests/unit/shapez_asteroid/test_mining_layout_route_costs.py) 보강

### P3-C — multi-outlet·target-role rewrite (2026-05-10)

- [x] `transport_connects_outlets_to_anchor`: **모든** outlet이 anchor transport 컴포넌트에 포함되는지 (`required.issubset(seen)`)
- [x] `mining_map_after_transport_reconstruction(..., target_role=want_role)`: 비대상 belt/pipe 보존
- [x] 단위: 전 outlet 연결·비대상 pipe 보존 테스트

### P3-D — Pass3 metric·replay 필드 (2026-05-10)

- [x] trace·요약: `pass3_transport_cells_removed_total`(target role 전체)·`pass3_internal_transport_saved`(final map `asteroid` ∩ transport)·내부 before/after count
- [x] `pass3_attempted_commit` / `pass3_final_committed` 분리 (greedy commit vs 최종 맵 채택)
- [x] 타임라인 `solver_pass3_transport` summary에 위 필드 전파
- [x] 검증: `pytest` 전체 449 passed / 1 skipped; `ruff check .`; `black --check .`·`mypy .` 통과 (`dj_database_url` stub·`tests/__init__.py` 패키지화·`tests.*` mypy 완화)

### P3-E1 — RouteZone + Lexicographic pathfinder (엔진만 · 2026-05-10)

**목표**: Pass3 greedy 대체용 reroute pathfinder를 **순수 함수**로 구현. **본 단계에서 `solver_service`·Pass3 greedy 교체·atomic replace·`MAX_ROUTE_LENGTH_RATIO` 게이트·protected corridor·replay UI 변경은 하지 않는다.**

- [x] `RouteZone`·`ROUTE_ZONE_COST`·`TransportKind`·`KIND_COST_MULTIPLIER`·[`route_zone.build_route_zone_map`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] [`lexicographic_router.find_lexicographic_route`](../archive/2026-05-mining-layout-v1-era/README.md)·`RouteSearchResult`·`max_expanded_nodes`·deterministic tie-break·고정 stub `path[0]==start`·선택 `allowed_cells`(무한 그리드 차단용, E2에서 솔버 bbox와 정합 가능)
- [x] 단위: 외곽(void) 우회가 길어도 `internal_transport_count`가 낮으면 선택
- [x] 단위: `placement_candidate` 직선을 피해 더 긴 경로
- [x] 단위: 동일 priority 시 경로(좌표 시퀀스) 사전순 결정적 선택
- [x] 단위: `blocked_cells` 미통과·stub 시작 유지
- [x] 단위: `max_expanded_nodes` 초과 시 `found=False`, `fallback_reason=expanded_node_budget_exceeded`
- [x] 단위: belt/pipe `KIND_COST_MULTIPLIER`가 `total_route_cost`에 반영
- [x] 검증: `pytest tests/unit/shapez_asteroid/test_lexicographic_router.py`·`ruff` 해당 파일

### P3-E1.1 — Lex router hardening (아키텍처 리뷰 · 2026-05-10)

**목표**: P3-E2 통합 전 정본 비용·solver 문자열 정합·방향 인식 탐색으로 디버깅 비용 점감.

- [x] [`ROUTE_ZONE_COST`](../archive/2026-05-mining-layout-v1-era/README.md) 3구역 스칼라를 정본(외곽 1·경계 5·내부 50)과 일치
- [x] [`TransportKind`](../archive/2026-05-mining-layout-v1-era/README.md) `shape_belt` / `fluid_pipe`·[`transport_kind_from_solver_value`](../archive/2026-05-mining-layout-v1-era/README.md)
- [x] [`find_lexicographic_route`](../archive/2026-05-mining-layout-v1-era/README.md) 탐색 상태 `(cell, previous_cell)` — 누적 turn이 진입 방향에 의존
- [x] 단위: 정본 비용·adapter·합류 셀 진입 방향에 따른 후속 turn (좌표 `x>=1`으로 `neighbors4` 제약 반영)
- [x] 검증: `pytest tests/unit/shapez_asteroid/`·`ruff`/`mypy`/`black` 변경 파일

### P3-E2 — Route adapter + Pass3 shadow lex vs greedy (베이스 · 2026-05-10)

- [x] [`route_adapter`](../archive/2026-05-mining-layout-v1-era/README.md) 입력/출력·`build_route_adapter_output`·Pass3 stub용 입력 빌더
- [x] [`pass3_transport`](../archive/2026-05-mining-layout-v1-era/README.md) shadow 전용 lex vs greedy probe·`p3e2_*` trace
- [x] [`solver_service`](../archive/2026-05-mining-layout-v1-era/README.md) 요약 병합 — **실맵 lex 커밋 없음**(greedy 유지)

### P3-E2.1 — shadow hardening (완료 · 2026-05-10, 문서 동기화)

- [x] `KIND_COST_MULTIPLIER`: `fluid_pipe`=1(정본 fluid=1 정합)
- [x] hard protected guard state(lex 경로·그림자 비교 시 침범 판별 가능)
- [x] greedy baseline `buildings` 전달(shadow 비교 정합)
- [x] `p3e2_pass3_summary_placeholder` 및 `p3e2_outlet_count` / `lex_success_count` / `greedy_success_count`
- [x] **`p3e2_shadow_would_commit`은 P3-E3 이전까지 실커밋 신호 아님** — shadow만; guarded 실커밋은 P3-E3
- [x] `current_plan.md`·본 체크리스트와 상태 정렬

### P3-E3 — Guarded lex commit (스켈레톤 승인 · 본구현 다음 · 2026-05-10)

**스켈레톤**: 기본 OFF·trace-only·기존 Greedy Pass3 불변(아키텍처 리뷰 승인).

**`p3e3_guarded_commit_enabled` 의미**(UI 혼동 방지용으로 고정 권장): `None` = Pass3/P3-E3 eligibility 이전에서 종료, `False` = guarded 경로 명시 비활성, `True` = guarded 활성(E3a: precheck trace+candidate 요약만·실맵 커밋은 E3b).

**본구현 권장 순서**: candidate DTO 고정 → guarded precheck trace만(`attempted=True` 등, 아직 커밋 없음) → atomic candidate map → `validate_final_mining_layout` → commit/rollback. fixed output stub·`MAX_ROUTE_LENGTH_RATIO`(1.35)·hard/soft protected(soft는 replacement 선계산 후 atomic replace) 필수.

**trace 분리 (반영·2026-05-10)**: `pass3_greedy_committed`·`p3e3_guarded_committed`(기존)·`pass3_map_accepted`(solver `validate_final` 통과 후 `map_try` 채택) — `pass3_committed`은 이후에도 **effective** Pass3 transport 커밋(하위 호환).

**체크리스트**

- [x] 기본 OFF 플래그 추가
- [x] Pass3 함수 인자 override 추가
- [x] `p3e3_*` trace placeholder 추가
- [x] solver `pass3_summary` 승격 추가
- [x] `precheck_*`·`guarded_disabled` reason 구분(E3a에서 `skeleton_noop` 제거)
- [x] guarded candidate DTO 고정(요약 필드·stub 좌표; `lex_routes_by_stub`/removed·added 셀 등은 E3b에서 확장)
- [x] guarded precheck만 추가(trace: `attempted=True`, `committed=False`, reject reason 세분화·`p3e3_guarded_precheck_candidate`)
- [x] guarded candidate map 생성·fixed stub 보존 gate
- [x] hard protected corridor reject
- [x] soft protected: replacement 선계산 후 atomic replace만
- [x] baseline route length / ratio(1.35) gate
- [x] `validate_final_mining_layout` gate·swap 후 post-commit 재검증·실패 시 greedy 스냅샷 rollback
- [x] 검증 통과 시에만 map rewrite·`p3e3_guarded_commit_committed=True`·실패 시 `p3e3_guarded_commit_rollback_*`
- [x] lex `found=False`·mixed kind 등 기존 skip·greedy 유지 정책과 정합 (shadow `p3e2_lex_found=False`면 E3b atomic 생략·`p3e3_guarded_atomic_skipped_reason`; mixed kind는 기존처럼 Pass3 조기 반환)
- [x] recovery context 아닐 때 `degraded_connected_recovery` 금지 (`run_pass3`·`allow_degraded_connected_commit=pass3_recovery_context`, 기본 `False`)
- [x] 단위: hard protected 침범 reject·ratio 위반·replacement 없음·post-commit validation 실패 rollback·개선+통과 시 commit·mixed kind skip 유지([`test_pass3_transport.py`](../../tests/unit/shapez_asteroid/test_pass3_transport.py))
- [x] **E3b-3 fixture 회귀**: 실레이아웃에서 자연 `would_accept=True`·`committed=True` snapshot ([`test_guarded_commit_accepts_real_layout_candidate_snapshot`](../../tests/unit/shapez_asteroid/test_pass3_transport.py))
- [x] 검증: `pytest` 476 passed / 1 skipped; `ruff check .`; `black --check .`; `mypy .` 통과 (P3-E3 ratio narrow 수정 후).
- [x] 2026-05-10 Asteroid solver 계약 보존 리팩터 후속: `pass1_timeline_integration`, `existing_layout_analysis`, `pass3_transport`, `reclaim_corridors`, `pass3_greedy_core`, `final_validation`, `pass12_bundle_commit`, `reclaim_soft_replace`, `lexicographic_router`에서 DTO/trace/helper만 분리. replay/trace field 이름, timeline frame id, protected corridor hard/soft 의미, reclaim budget/route selection 의미 변경 없음. 검증: `python -m pytest tests/unit/shapez_asteroid/` → 291 passed, 1 skipped; `python -m pytest tests/integration/web/test_web_smoke.py tests/unit/shapez_asteroid/test_copy_preview.py` → 29 passed; `ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout tests/unit/shapez_asteroid`; `mypy django_apps/shapez_asteroid/services/asteroid_mining_layout`; `black --check django_apps/shapez_asteroid/services/asteroid_mining_layout tests/unit/shapez_asteroid`.

### Pass12 preserve-quality 텔레메트리 (2026-05-11)

- [x] `recovery_orchestrator`: `max_cycles` 최소 1 (패치 불일치 시 무실행 루프 방지).
- [x] 재현용 NDJSON 5 + `striped_greenfield_bp.json` → [`tests/fixtures/pass12_telemetry_trace_pack/`](../../tests/fixtures/pass12_telemetry_trace_pack/); aggregate + A/B 실행; 정책 요약 → [`documents/ai/pass12_telemetry_policy_note_2026-05-11.md`](pass12_telemetry_policy_note_2026-05-11.md).
- [x] 검증: `pytest tests/unit/shapez_asteroid/` 467 passed; 변경 파일 `ruff`/`black --check`/`mypy` (전체 ruff·black은 기존 이슈 가능).

### 문서 lifecycle 계층화 (2026-05-12)

- [x] [`documents/index/document_lifecycle.md`](../index/document_lifecycle.md): `CANON` / `ACTIVE` / `COMPLETED` / `ARCHIVED` / `RESEARCH` / `REPORT` / `SUPERSEDED` 상태 enum과 읽기 우선순위 추가.
- [x] [`documents/index/document_inventory.md`](../index/document_inventory.md): 주요 정본·활성·연구·보고·보관 문서 상태표 추가.
- [x] [`AGENTS.md`](../../AGENTS.md)·[`documents/README.md`](../README.md): 문서 authority 라우팅 연결.
- [x] [`documents/ai/START_HERE.md`](START_HERE.md): 새 AI 세션·서브에이전트용 context 진입점 추가.
- [x] [`documents/adr/`](../adr/): bounded recovery, protected corridor, final validation, replay cycle stream ADR 초기 골격 추가.
- [ ] `documents/canon/` 물리 분리 플랜 작성: 현재 정본 경로 링크 영향과 이동/리다이렉트 전략 확정 필요.
- [ ] `documents/reports/YYYY-MM/` 분리 플랜 작성: debug/progress/report 성격 문서 이동 전 참조 링크 확인 필요.

### Pass2 island fallback gate / STEP4 reentry telemetry (2026-05-13)

- [x] 작업 유형: `solver` / `tests`
- [x] 플랜: [`documents/plans/plan_pass2_island_fallback_gate_2026-05-13.md`](../plans/plan_pass2_island_fallback_gate_2026-05-13.md)
- [x] 범위: Pass2 `transport_cells_before_island_fallback` 허용 조건 축소, STEP4 `step4_reentry_index` telemetry 추가
- [x] 검증: 영향 단위 테스트, 관련 STEP4/Pass2 테스트, ruff, black --check, mypy 실행

### 2026-05-13 asteroid_mining_layout DTO 인벤토리

- [x] 작업 유형: `solver` / `refactor` / 문서 승인용 인벤토리
- [x] 문서: [`plans/mining_layout_dto_inventory_2026-05-13.md`](../archive/2026-05-mining-layout-v1-era/ai-plans/mining_layout_dto_inventory_2026-05-13.md)
- [x] 범위: `03_data_schema_dto.md` E절과 `existing_layout_analysis`, STEP4 실패 상세, timeline/replay, Pass12 probe의 느슨한 `dict[str, Any]` 경계를 대조
- [x] 구현: 공유 mining-map row 타입, ExistingLayout wire 타입, STEP4 failure detail wire 타입, Pass12 probe stats/trace 타입 추가
- [x] 적용: final validation / existing layout / STEP4 detail / Pass12 probe의 읽기 경계 타입 힌트 적용. public dict 반환 계약과 serialization key order는 유지.

### 2026-05-13 asteroid_mining_layout DTO contract hardening phase 2

- [x] 작업 유형: `solver` / `refactor` / semantic contract hardening
- [x] 구현: `RecoveryTrigger` / `CommitReason` / `RollbackReason` / `RejectedReason` DTO namespace 추가
- [x] 적용: `semantic_contracts.partition_pass3_commit_reason_payload`가 DTO namespace classifier를 경유하도록 변경
- [x] 적용: STEP4 routing failure row를 typed DTO/public dict adapter 경유로 생성. 기존 public key set 유지.
- [x] 회귀: commit_reason 성공 namespace, misfiled rejected_reason promotion, routing failure row key snapshot, ExistingLayoutAnalysis vs FinalValidationReport 필드 분리 테스트 추가
# 2026-05-15 문서 구조 자동 갱신

- [x] `structure.md`에 v2 asteroid 서비스 트리와 `tests/unit/shapez_asteroid_v2/` 반영
- [x] `documents/README.md`에서 `debug/`, `reports/`, `refactory/`, v2 active 문서, v1 archive 판정 갱신
- [x] `documents/index/document_inventory.md`에서 `CANON` / `ACTIVE` / `RESEARCH` / `REPORT` / `ARCHIVED` 상태 재분류
- [x] `documents/archive/README.md`와 `archive/2026-05-mining-layout-v1-era/README.md` 최신 archive 정책 갱신
- [x] 새 파일 이동 없음: v2 문서는 active/canon/report로 유지하고, v1-era 묶음만 archive로 유지
- [x] 2026-05-15 추가 갱신: v2 corridor probe/recovery 구조, report index, supplemental STEP4 문서 권위(`ACTIVE`, 정본 아님) 반영
