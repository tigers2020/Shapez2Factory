# 코드-문서 교차검증

> 생성: 2026-05-15. production code는 수정하지 않았다. 기준 정본은 `documents/Algorithm/mining_solver_cursor_sessions/README.md`와 01-14 step docs다.

## STEP별 현재 코드 대응

| canonical STEP | 대응 모듈 | 현재 상태 |
|---|---|---|
| STEP 0 decode | `decode/copy_decode_adapter.py`, `solver.py::build_copy_preview_v2_sidecars` | copy-preview 경로에서 사용. |
| STEP 0.5 ExistingLayoutAnalysis | `decode/existing_layout_analysis.py`, `domain/existing_layout.py` | read-only context로 구현. |
| STEP 1 reconstruction | `reconstruction/asteroid_reconstruction.py`, `reconstruction/patch_interior.py`, `domain/reconstruction.py` | mineable_placement_cells 생성 담당. |
| STEP 2 Pass1 | `placement/pass1_outer.py`, `placement/bundle_candidate.py` | cheap escape probe + provisional placement 구현. |
| STEP 3 Pass2 | `placement/pass2_internal.py` | Pass1 blocked set 기반 provisional placement 구현. |
| STEP 4 routing | `routing/merge_aware_router.py`, `routing/trunk_seed.py`, `routing/connectivity.py`, `domain/routing.py` | DTO/utility/skeleton. full routing 미구현. |
| STEP 5 Pass3 | 없음 또는 enum/DTO 일부 | 현재 v2 코드에 전용 Pass3 구현 미확인. |
| STEP 6 Reclaim | 없음 또는 enum/DTO 일부 | 현재 v2 코드에 전용 reclaim loop 미확인. |
| STEP 7 optional post-reclaim Pass3 rerun | 없음 | 미구현. |
| STEP 8 Recovery branch | `domain/enums.py`, `domain/routing.py`, `domain/orchestration.py`, `domain/trace_semantics.py` | trigger/DTO/semantic guard는 있음. bounded branch orchestration은 미구현. |
| STEP 9 Final validation | `validation/final_validation.py`, `domain/validation.py` | assertion-only skeleton. 일부 leniency 존재. |
| STEP 10 Replay/UI | `replay/trace_event.py`, `replay/snapshots.py`, `preview_reconstruction_timeline.py`, `serialization/*` | output/preview/adapters 중심. algorithm input 아님. |

## v1/v2 판단

- v2/current: `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/`, `tests/unit/shapez_asteroid_v2/`.
- legacy/v1-era 또는 legacy-adjacent: archive 문서가 가리키는 `asteroid_mining_layout/` 경로는 현재 tree에 없고, 일부 non-v2 support service(`asteroid_reconstruction.py`, `asteroid_patch_interior.py`)가 남아 있다.
- output/debug stack: `behavior_artifact_collector.py`, `v2_behavior_artifact_dump.py`, `copy_preview_debug_dump.py`, `replay/*`, `serialization/*`, `preview_reconstruction_timeline.py`.

## 기능별 모듈

| 질문 | 현재 코드 경로 |
|---|---|
| replay/debug/NDJSON/solver_summary를 읽는 모듈 | `replay/snapshots.py`는 `read_ndjson_replay_events` stub만 두고 NotImplementedError. `preview_reconstruction_timeline.py`는 NDJSON/solver_summary를 읽지 않는다고 명시. output artifact stack은 `behavior_artifact_collector.py`/serialization. |
| route를 만드는 모듈 | full route 생성은 `MergeAwareRouter.route_all` skeleton. `routing/connectivity.py`는 flood utility, `trunk_seed.py`는 seed skeleton. |
| validation 수행 모듈 | `validation/final_validation.py::validate_final_layout_stub`. |
| recovery 수행 모듈 | 현재 v2에서 bounded recovery 실행 orchestration은 미확인. enum/trace DTO는 있음. |
| placement state를 mutate/생성하는 모듈 | `placement/pass1_outer.py`, `placement/pass2_internal.py`, `placement/placement_fsm.py`. 함수는 `ctx`를 mutate하지 않고 결과 DTO/commit entries를 만든다. |
| replay/trace only 모듈 | `replay/trace_event.py`, `replay/snapshots.py`, `runtime/trace_events.py`, `serialization/*`, `preview_reconstruction_timeline.py`. |

## Findings

| id | code path | canonical doc path/section | observed behavior | expected behavior | severity | recommended next action | code change required later |
|---|---|---|---|---|---|---|---|
| CDA-001 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py` | `04_step0_decode.md`, `03_data_schema_dto.md` ExistingLayoutAnalysis | read-only analysis로 작성되어 있고 mineable field를 만들지 않으며 belt/pipe를 별도 TransportKind로 분석한다. | ExistingLayoutAnalysis는 read-only context이며 mineable_placement_cells를 만들지 않는다. | info | 현 계약 유지. | no |
| CDA-002 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py` | `05_step1_reconstruction.md` | module docstring과 DTO가 `mineable_placement_cells`를 STEP1 산출로 정의한다. `DecodedExistingLayoutContext`는 API symmetry 용도라고 명시한다. | Reconstruction alone creates mineable_placement_cells. | info | 테스트와 문서 링크 유지. | no |
| CDA-003 | `placement/pass1_outer.py`, `placement/pass2_internal.py` | `06_step2_pass1_placement.md`, `07_step3_pass2_placement.md`, `08_step4_routing.md` | cheap escape는 probe-only로 명시되고 commit entries는 `PROVISIONAL_PLACED`만 생성한다. | Pass1/Pass2 produce provisional placement only; cheap escape path is not final route. | info | `test_pass1_pass2_provisional_contract.py` 유지. | no |
| CDA-004 | `placement/placement_fsm.py` | `08_step4_routing.md` PlacementCommitState FSM | PROVISIONAL → ROUTED_CONFIRMED/QUARANTINED/ROLLED_BACK 전이 helper가 있고 Pass1/Pass2 provisional apply helper가 있다. | PlacementCommitState FSM respected; STEP4 owns route confirmation. | info | STEP4 구현 시 이 helper를 유일한 전이 게이트로 사용. | yes, when STEP4 implemented |
| CDA-005 | `routing/merge_aware_router.py`, `routing/trunk_seed.py` | `08_step4_routing.md` | full STEP4 routing과 trunk seed는 NotImplementedError skeleton이다. | STEP4 starts routing from fixed output stub and owns route confirmation. | blocker | 구현 전까지 v2 full solve를 완료로 선언하지 말 것. 다음 구현 prompt에서 STEP4를 별도 phase로 계획. | yes |
| CDA-006 | `routing/connectivity.py`, `validation/final_validation.py` | `13_step9_validation.md` | final validation skeleton은 quarantined count와 optional connectivity probe만 수행하고, exterior seed가 없으면 connectivity를 lenient true로 둔다. | Final validation is assertion-only and should not repair state; full hard checks are expected. | medium | skeleton leniency를 문서에 명시하고, STEP9 hard check 구현 계획을 별도 작성. | yes |
| CDA-007 | `domain/enums.py`, `domain/trace_semantics.py`, `runtime/trace_events.py` | `11_step8_recovery.md` §13.5, `14_step10_replay_ui.md` §16.3 | `RecoveryTrigger`와 `CommitReason`이 분리되어 있고 `recovery_trigger`를 `commit_reason`으로 쓰지 못하게 guard한다. | recovery_trigger and commit_reason separated. | info | 현 semantic guard 유지. | no |
| CDA-008 | `replay/snapshots.py`, `preview_reconstruction_timeline.py`, `solver.py` | `14_step10_replay_ui.md` | NDJSON reader는 offline tooling stub이며 solver/copy-preview path는 replay/NDJSON을 algorithm input으로 읽지 않는다고 명시한다. | Replay/trace/NDJSON are output-only. | info | import-boundary tests 유지. | no |
| CDA-009 | `domain/enums.py`, `bundle_candidate.py`, `existing_layout_analysis.py` | `03_data_schema_dto.md`, `08_step4_routing.md` | `TransportKind.SHAPE_BELT`와 `FLUID_PIPE`가 별도 enum이고 existing layout analysis도 kind별 component로 나눈다. | Belt and pipe are separated by TransportKind. | info | Route-level mixed kind 금지 테스트 유지. | no |
| CDA-010 | `asteroid_mining_layout_v2/` 전체 | `09_step5_pass3_transport.md`, `10_step6_reclaim_loop.md`, `11_step8_recovery.md`, `12_protected_corridor.md` | Pass3/Reclaim/Protected corridor lifecycle의 executable v2 module은 아직 확인되지 않는다. enum/rejected reason 일부만 있음. | Pass3, Reclaim, bounded Recovery, hard/soft/candidate corridor lifecycle are explicit phases/contracts. | high | implementation cleanup 전에 미구현 범위를 `documents/ai/current_plan.md` 또는 새 plan에 분리. | yes |
| CDA-011 | `documents/Algorithm/mining_solver_cursor_sessions/README.md` | canonical index itself | canonical README에 사용자 지정 01-14 범위를 벗어난 `14_step4_routing_dto_refactor_inventory.md`, `15_step4_telemetry_field_semantics.md`가 함께 나열되어 있다. | canonical authority list is stable and unambiguous. | medium | 두 문서를 supplemental/unknown으로 표기하거나 별도 section으로 분리. | no |
| CDA-012 | `documents/archive/2026-05-mining-layout-v1-era/**` | all canonical docs | archive에는 old `asteroid_mining_layout/` 경로, latest.ndjson 기반 분석, v1 assumptions가 다수 남아 있다. | Historical reports must not override canonical specs. | medium | archive README와 inventory에서 historical-only 라벨 유지. | no |
