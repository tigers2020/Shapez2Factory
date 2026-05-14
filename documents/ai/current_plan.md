# 현재 계획 (Current plan)

작업 시작 시 채우고, 범위가 바뀔 때마다 갱신한다.

## 목표 (갱신 2026-05-14)

- **(범위 2, 진행 중)** 채굴 파이프라인 **v2 단일 권위** — Cursor 실행 플랜 `mining_pipeline_v2_authority` (저장소 밖 `.cursor/plans/`에 생성됨; 본 절이 워크스페이스 앵커). 단계는 ACTIVE MVP §3·§4와 동일: **웹 플래그·copy-preview v2 분기(PR-G) → 전부 green → PR-H v1 패키지 리네임**.
- **(ACTIVE, 2026-05-13)** 채굴 솔버 **v2 그린필드 MVP** 실행 순서·게이트: [`plans/mining_solver_v2_mvp_execution_2026-05-13.md`](plans/mining_solver_v2_mvp_execution_2026-05-13.md) — **런타임 v1 import는 2026-05-14 제거됨**; 문서의 «v1 → `_old` 물리 리네임» 단독 PR은 아카이브·히스토리용으로만 잔존 가능.
- **레거시 웹·preview 의존 감사(REPORT)**: [`../reports/2026-05/asteroid_legacy_preview_stack_audit.md`](../reports/2026-05/asteroid_legacy_preview_stack_audit.md).
- `shapez_asteroid` 1단계 스켈레톤·복사 미리보기·채굴 레이아웃 솔버(멀티패스·pass3 transport 등)까지 **구현 완료**로 본다.
- 리포 전체 **로컬 품질 게이트**(`pytest` / `ruff` / `mypy` / `black --check`)를 통과한 상태를 유지한다.
- **진행 중 (정본)**: 채굴 레이아웃 솔버 **안정화** — 생산 설비 보존·비철거 복구·성공 판정 고정 ([`mining_layout_solver_stabilization_2026-05-09.md`](plans/mining_layout_solver_stabilization_2026-05-09.md)). 1차는 P0(요약·최종 검증·철거형 merge repair 차단)부터.
- **반영됨 (2026-05-10, Stabilization-P0/P1 일부)**: `solver_trace.emit_solver_summary_once`·`trace_run_scope` 요약 1회, [`final_validation.validate_final_mining_layout`](django_apps/shapez_asteroid/services/asteroid_mining_layout/final_validation.py), [`solver_service.build_solver_timeline`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py)(`after_pass2` 베이스라인은 타임라인 proxy), [`bundle_route_probe_or_reject`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py)·`bundle_reject_no_route` trace. 철거형 merge 차단·destructive 카운트 등 안정화 플랜 나머지 항목은 미진행.
- **Stabilization-P1 (배치 훅)**: `_commit_bundle_with_stub_to_trunk_route_probe` 명칭 대신 공개 헬퍼 `bundle_route_probe_or_reject`.
- **Canonical P1-A / P1-B / P1-C (반영됨)**: Pass1 outer-first·[`enumerate_extension_topologies`](django_apps/shapez_asteroid/services/asteroid_mining_layout/extension_topology.py)·출력 방향 메타·출구 스텁 검증·P1 cheap void 마진(바운딩 박스 기준 3~7)·Pass2는 transport-only 프로브.
- **Pass2-A internal fill MVP (반영됨)**: [`pass2_internal_placement.run_pass2_internal_placement_mvp`](django_apps/shapez_asteroid/services/asteroid_mining_layout/pass2_internal_placement.py) — Pass1 이후 남은 mineable에 inner-first 배치, 커밋은 `try_commit_pass2_bundle`만. [`pass1_timeline_integration`](django_apps/shapez_asteroid/services/asteroid_mining_layout/pass1_timeline_integration.py)에서 Pass1 직후 실행·`solver_summary`에 `pass2_*` 필드 병합.
- **P2-A STEP4 최소 merge-aware routing (반영·마감 2026-05-09)**: [`run_step4_merge_aware_routing`](django_apps/shapez_asteroid/services/asteroid_mining_layout/step4_merge_routing.py)·`solver_service` 연동. 품질 게이트: `pytest` 141 passed / 1 skipped, `ruff` 통과(`I001` 정렬만).
- **P2-B PlacementCommitState FSM (반영·계약 보강 2026-05-10)**: `placement_commit`·Pass12 `placement_records`·STEP4 전이·rollback·`routing_failures` 계약 필드·`final_validation` 격리 탐지·요약/프레임 카운트. **P2-B.1(2026-05-10, DONE)**: `unfinalized_placement_count`·`return_reason` 가드·맵 행 FSM 메타·STEP4 입력 행 복사. **P2-B.1 polish(2026-05-10, DONE)**: `layout_degraded`에 `step4_rollback_count` 반영·`solver_summary`에 `step4_rolled_back_count`·예외 경로 `setdefault`.
- **P2-C + P2-C.1 (반영·마감 2026-05-10)**: `_p2c_revalidate_and_correct`·요약 메타·실맵 회귀 [`test_step4_cascade_revalidates_route_after_neighbor_rollback`](../../tests/unit/shapez_asteroid/test_step4_merge_routing.py)·`pytest.ini`에 `--import-mode=importlib`.
- **P3-A ~ P3-D (반영·2026-05-10)**: STEP4 이후 Pass3 greedy transport 축소 MVP — `solver_service` 연동·최종 검증 롤백·void 비연속·전 outlet 연결·`target_role` rewrite만·mixed kind skip·`pass3_transport_cells_removed_total` / 내부 `pass3_internal_transport_saved`·`pass3_attempted_commit`·`pass3_final_committed`·타임라인 요약. **다음 솔버 단계(선택)**: **P3-E** 문서 정본 lexicographic reroute / RouteZone (별도 설계·플랜 권장).
- **P3-E1 (범위 잠금·2026-05-10, 아키텍처 검토 반영)**: RouteZone + lexicographic pathfinder를 **순수 함수 모듈**로만 구현한다. **본 단계에서 `solver_service`·기존 Pass3 greedy 삭제 플로우·`MAX_ROUTE_LENGTH_RATIO` 게이트·replay UI에는 연결하지 않는다.** 성공 기준은 단위 테스트·정적 계약(고정 stub = `path[0]`, blocked 미통과, 동일 입력 동일 경로, `max_expanded_nodes` 초과 시 `found=False`). 구현 위치: [`route_zone.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/route_zone.py), [`lexicographic_router.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/lexicographic_router.py). 통합(P3-E2/E3)은 별도 게이트.
- **P3-E1.1 (반영·2026-05-10, 솔버 아키텍처 리뷰)**: DTO 정본과 동일한 3구역 `ROUTE_ZONE_COST`(1/5/50). `TransportKind` 값을 `shape_belt`/`fluid_pipe`로 solver와 정렬·[`transport_kind_from_solver_value`](django_apps/shapez_asteroid/services/asteroid_mining_layout/route_zone.py). Lex 탐색 상태를 `(cell, prev)`로 두어 turn 축이 진입 방향을 반영. 확장 구역(FILLABLE·PLACEMENT 등)·Pass3 연결은 **P3-E2 플랜**에서.
- **P3-E2 (베이스·2026-05-10)**: [`RouteAdapterInput` / `RouteAdapterOutput`](django_apps/shapez_asteroid/services/asteroid_mining_layout/route_adapter.py)·`build_route_adapter_output`·`route_adapter_input_for_pass3_stub`. Pass3 [`run_pass3_transport_minimization_from_maps`](django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3_transport.py)에 **shadow 전용** lex vs greedy probe·`p3e2_*` trace·`solver_service` 요약 병합. **아직** lex 경로로 맵 커밋·Pass3 greedy 교체는 하지 않음.
- **P3-E2.1 (완료·2026-05-10) — shadow hardening**: `KIND_COST_MULTIPLIER`에서 `fluid_pipe`=1(정본 fluid=1 정합)·hard protected guard state·greedy baseline buildings 전달·`p3e2_pass3_summary_placeholder`·`p3e2_outlet_count` / `lex_success_count` / `greedy_success_count`. **`p3e2_shadow_would_commit`은 P3-E3 이전까지 실커밋 신호가 아님**(shadow만; guarded 실커밋은 P3-E3).
- **P3-E3 — Guarded lex commit (마감·2026-05-10, 체크리스트 [`checklist.md`](checklist.md) §P3-E3)**: 기본 OFF·opt-in `p3e3_guarded_commit_enabled`. **P3-E3 final gate**: `pass3_transport._p3e3_build_atomic_candidate_map` ratio 계산 mypy narrow 수정 후 전역 `mypy .` clean.
  - **P3-E3a (반영·2026-05-10)**: `P3E3GuardedPrecheckCandidate` + `_p3e3_emit_guarded_trace` — precheck만(`p3e3_guarded_commit_attempted=True`, `precheck_*`·`p3e3_guarded_precheck_candidate`); per-stub lex 좌표·맵 델타는 **E3b**.
  - **P3-E3b-1 / E3b-2a (반영·2026-05-10)**: atomic candidate map·fixed stub·hard/soft·`MAX_ROUTE_LENGTH_RATIO`(1.35)·커밋 전 `validate_final_mining_layout`·`would_accept` 게이트·성공 시 transport swap. **`commit_reason`**: `guarded_atomic_candidate` (`COMMIT_REASON_GUARDED_ATOMIC`) — greedy의 `normal_gain` / `degraded_connected_recovery`와 별도 네임스페이스.
  - **P3-E3b-2b (반영·2026-05-10)**: swap 직후 post-commit 동일 검증 실패 시 **greedy `known_good_transport_snapshot`(role map 포함)으로 즉시 복원**·`p3e3_guarded_commit_rollback_*`·`p3e3_guarded_post_commit_validation_passed` trace.
  - **P3-E3b-3 (반영·2026-05-10)**: 실레이아웃 fixture(`_decoded_miners_with_belt_escape`)에서 `would_accept=True`·post-commit 통과 → `commit_reason=guarded_atomic_candidate` 자연 발생 회귀 고정 ([`test_guarded_commit_accepts_real_layout_candidate_snapshot`](../../tests/unit/shapez_asteroid/test_pass3_transport.py)). 후보 셀(37)·removed(2)·added(18)·baseline=candidate=38·ratio=1.0·preserved stub=2 snapshot, guarded ON ≠ OFF cell-set 차이 보존.
  - **P3-E3 체크리스트 잔여 (반영·2026-05-10)**: shadow `p3e2_lex_found=False`면 E3b atomic 생략(`p3e3_guarded_atomic_skipped_reason`, mixed kind 조기 반환과 greedy-only 정합). `pass3_recovery_context=True`일 때만 greedy `allow_degraded_connected_commit` 전달 — 기본 경로에서 `degraded_connected_recovery` 금지.
  - **trace 분리 (반영·2026-05-10)**: `pass3_greedy_committed`(`pass3_transport`)·`p3e3_guarded_committed`(기존)·`pass3_map_accepted`(`solver_service` post-validate 채택); `pass3_committed`은 effective 유지.
- **계약 보존 리팩터 1차 (반영·2026-05-10)**: [`solver_service.build_solver_timeline`](django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py)는 공개 진입점·호환 patch 경로를 유지하고, 내부 Pass12/STEP4/Pass3/P4/finalize 조립만 `solver_pipeline/`로 분리. replay v2·timeline frame id·`routing_state` protected corridor shape·phase order 의미 변경 없음.
- **P0.5 ExistingLayoutAnalysis (문서 정본·2026-05-10)**: 디코드 island JSON이 raw asteroid가 아닌 **기존 mining layout**인 경우 `source_kind`, SpacePipe(또는 belt) connected components, miner–transport 부착, orphan transport issues를 생성하고, copy-preview / API / UI / solver **hint context**의 공통 입력으로 쓴다. DTO·파이프라인 슬롯: [`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) §E, [`04_step0_decode.md`](../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md) §5.4, 플랜 [`../plans/decoded_existing_layout_model.md`](../plans/decoded_existing_layout_model.md). **Pass3 trunk 보호 정책 구현**은 별도 단계; `ExistingLayoutSolverHints` 계약만 선행 고정.
- **다음 후보(솔버)**: 정본 문서에 맞춘 corrective recovery / `SolverRunContext` 도입 여부는 별도 플랜. ([`merge_repair_not_found_recovery_2026-05-09.md`](plans/merge_repair_not_found_recovery_2026-05-09.md)), mineable 2차 탐색 P1 ([`merge_repair_mineable_route_p1_2026-05-09.md`](plans/merge_repair_mineable_route_p1_2026-05-09.md)) — 안정화 플랜과 충돌 시 **안정화 플랜(P1 철거 차단 등)이 우선**.

## 범위

- **완료로 보는 것**: `INSTALLED_APPS`, health·copy-preview·optimize API, `asteroid_mining_layout` 서비스 모듈, 단위 테스트, strict i18n에 필요한 asteroid API `gettext` 키(`build_locale_ko.py` KO dict).
- **제외(여전히)**: Gurobi·MIP 본체, `shapez_solver`와의 직접 결합.

## 게이트

- [x] 리서치/플랜: 스켈레톤·소행성 추출·레이아웃 플랜 합의
- [x] 사람 승인: 해당 플랜 기준 구현
- [x] **PR-H (런타임 v1 차단)**: **2026-05-14 선행 반영** — `copy_preview`·`views`·`blueprint_map_summary`에서 `django_apps.shapez_asteroid.services.asteroid_mining_layout` import 제거; 보관용 스텁 `asteroid_mining_layout_v1_deprecated/`. 문서상 «물리 리네임·대규모 치환» 단독 PR은 별도로 남을 수 있음.
- [x] 리서치/플랜: merge `repair not_found` 복구 ([`research_merge_repair_not_found_2026-05-09.md`](../research/research_merge_repair_not_found_2026-05-09.md), [`plans/merge_repair_not_found_recovery_2026-05-09.md`](plans/merge_repair_not_found_recovery_2026-05-09.md)) — 사용자 진행 지시로 승인 간주
- [x] 리서치/플랜·승인: 솔버 안정화 ([`plans/mining_layout_solver_stabilization_2026-05-09.md`](plans/mining_layout_solver_stabilization_2026-05-09.md)) — 정식 반영·구현 착수 허용

## 다음 후보 (우선순위)

0. **Pass2 spine soft 우선순위 A/B (반영·2026-05-10)**: [`plans/pass2_spine_soft_priority_ab_2026-05-10.md`](plans/pass2_spine_soft_priority_ab_2026-05-10.md). `mineable_inner_first_order` / `run_pass2_internal_placement_mvp` / `integrate_pass12_placement_into_working_map`에 `priority_seeds` · `pass2_spine_priority_enabled` 인자 추가, `solver_summary["pass2_spine_priority_applied"]` 노출. **기본 OFF**(솔버 외부 호출은 always-OFF), 단위 테스트만 ON. 회귀 4건·전체 302 passed/1 skipped, 변경 5파일 `ruff`/`mypy`/`black --check` clean. 다음 단계로는 시드 활용 깊이 B(stub 방향 우선) / C(monotone path 후보)와 §13.5 Recovery trigger 확장이 후보.
1. **STEP 6 P4(갱신·2026-05-10 후반)**: `run_p4_reclaim_loop_after_pass3`에 shadow·P4-B1·P4-B2·bounded loop·§14.3 `_try_atomic_replace_soft_corridor` hook·`p4_soft_replace_attempt_count`/`commit_count` 반영됨. **추가 반영**: Step4 커밋 route path를 `routing_state` hard/soft 보호 복도 풀로 공급하고 P4 reclaim이 solver pool로 수신. **soft replace v2 반영**: routing jobs 전체를 deterministic order로 순회하고 첫 valid replacement만 atomic commit, job count/index/reject reasons trace 추가. **UI/summary 반영**: soft repair session 누적과 마지막 session job trace를 분리 표시, old/new cells overlay 추가. **다음**: capacity/recovery/실데이터 회귀.
2. **capacity rated overflow·recovery·실데이터 회귀**: P4 이후 스트림으로 병행 검토.
3. **STEP4 이후 확장**: 용량·trunk 시드·`solver_validate`와의 의미 정렬(`validation_connectivity_failed` vs P1 cheap feasibility 등).
4. **`scripts/build_locale_ko.py` WARN**: django 도메인에 KO 미매핑 문자열 다수(템플릿/솔버 UI 문구). 점진적으로 `KO` dict·`trans` 보강.
5. **원격 동기화**: 브랜치가 `origin/master`보다 ahead이면 `git push`로 반영.
6. **미추적 자산**: `django_apps/web/static/web/assets/shape_part_sprites/*.png` — 의도된 생성물이면 커밋·아니면 `.gitignore` 또는 삭제 정리.

## 메모

- **P3-E3 final gate**: 전역 `mypy .` clean — `pass3_transport._p3e3_build_atomic_candidate_map`에서 `baseline_route_length`/`candidate_route_length`를 지역 변수로 두고 `is not None`·`!= 0`으로 narrow.
- `shapez_asteroid` ↔ `shapez_solver` 상호 import 금지. `locale/ko/LC_MESSAGES/django.mo`는 `.gitignore`이므로 배포/CI에서 `build_locale_ko.py`로 생성한다.
- **계약 보존 리팩터 후속(반영, 2026-05-10)**: `pass1_timeline_integration`, `existing_layout_analysis`, `pass3_transport`, `reclaim_corridors`, `pass3_greedy_core`, `final_validation`, `pass12_bundle_commit`, `reclaim_soft_replace`, `lexicographic_router`에서 DTO/trace/helper 책임만 분리. replay/trace field 이름, timeline frame id, protected corridor hard/soft 의미, reclaim budget/route selection 의미 변경 없음.
