# 리팩토링 문서 인덱스

shapez2Solver **채굴 레이아웃 솔버** 관련, 문서 정본(`documents/Algorithm/mining_solver_cursor_sessions/`)·코드 감사·아키텍처 리뷰를 바탕으로 한 **목표별 리팩토링/정렬** 메모다. 구현 전 플랜 승인·범위 확정이 필요하다.

## 상위 Epic(묶음) → 상세 티켓

| Epic | 파일 | 다루는 범위 | 하위 상세 문서 |
|------|------|-------------|----------------|
| A | [control-flow-refactor.md](./control-flow-refactor.md) | §4.3 복귀·오케스트레이터·attempt 분리 | 02, [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md), [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md), [epic_a_implementation_scope.md](./epic_a_implementation_scope.md) |
| B | [semantic-fields-refactor.md](./semantic-fields-refactor.md) | `recovery_trigger` / `commit_reason` / rollback·reject | 03, 07 |
| C | [corridor-state-machine-refactor.md](./corridor-state-machine-refactor.md) | candidate/soft/hard·atomic replace | 04, 14 |
| D | [trace-layer-isolation.md](./trace-layer-isolation.md) | replay·NDJSON·summary = 출력 계층 | 06, 16 |

**Cursor 실행 순서(YAML 스케치):** [cursor_work_phases.md](./cursor_work_phases.md) (Phase 0–4 + Placement FSM 안내)

**Phase 0 산출물(읽기 전용 drift matrix):** [phase0_drift_matrix.md](./phase0_drift_matrix.md) — PR #2 병합 후 **증거 보강**은 브랜치 `audit/phase0-drift-evidence`에서 진행 가능.

## 리뷰어 합의: 회귀 우선순위(요약)

정본 방향은 유지하고, **구현이 trace/recovery/replay 계층과 제어 흐름이 섞이며 drift** 난 구간을 되돌린다.

1. **의미 네임스페이스** — `recovery_trigger` / `commit_reason` / `rollback_reason` / `rejected_reason` / `event_type` (Epic **B**)
2. **Recovery 제어 흐름** — §4.3 trigger별 복귀 (Epic **A**)
3. **Protected corridor 상태 머신** — §14 (Epic **C**)
4. **PlacementCommitState** — merged seed 예외·§9.6 (문서 **05**; Epic A/B와 순서 조율)
5. **Trace 계층 격리** — 알고리즘 입력으로의 read 금지 (Epic **D**)

## 상세 문서 목록 (01–16 + Epic A mini-audit)

| 문서 | 목표 요약 |
|------|-----------|
| [01_canonical_doc_paths.md](./01_canonical_doc_paths.md) | 정본 문서 경로 혼동 제거·인덱스 |
| [02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md) | §4.3 트리거별 복귀 vs 오케스트레이터 단순화 정렬 |
| [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) | Epic A 진입 전 §4.3 vs 코드 1차 감사 표·식별자 사전 |
| [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) | §4.3 대비 **B(MVP 예외)** 트리거만 고정 표 |
| [epic_a_implementation_scope.md](./epic_a_implementation_scope.md) | Epic A **구현 PR** 허용·금지·정본 근거(스코프 drift 방지) |
| [03_recovery_trace_namespaces.md](./03_recovery_trace_namespaces.md) | `recovery_trigger` / `commit_reason` / `rollback_reason` 계약 |
| [04_protected_corridor_lifecycle.md](./04_protected_corridor_lifecycle.md) | hard/soft/candidate 생명주기·STEP4 요약 블록 |
| [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md) | merged seed 시 `ROUTED_CONFIRMED` 예외·§9.6 정합 |
| [06_replay_timeline_frames.md](./06_replay_timeline_frames.md) | `SOLVER_TIMELINE_FRAME_ORDER`·P4 가시성·§16.2 |
| [07_pass3_commit_reason_contract.md](./07_pass3_commit_reason_contract.md) | Pass3 `commit_reason` 확장 vs §13.5 |
| [08_existing_layout_analysis_immutability.md](./08_existing_layout_analysis_immutability.md) | STEP 0.5 산출물 불변·DTO화 |
| [09_pass12_cheap_escape_probe_contract.md](./09_pass12_cheap_escape_probe_contract.md) | Pass1/2 cheap escape·probe가 occupied/route에 오염되지 않음 |
| [10_step4_trunk_seed_vs_goal_set.md](./10_step4_trunk_seed_vs_goal_set.md) | trunk seed vs route goal set 역할 분리 유지 |
| [11_trunk_load_observation_contract.md](./11_trunk_load_observation_contract.md) | `trunk_load` 1차 합산 관측·hard gate 비사용 유지 |
| [12_pass3_lexicographic_priority.md](./12_pass3_lexicographic_priority.md) | Pass3 사전순 튜플·§10.4·`lexicographic_router` 정합 |
| [13_fixed_output_stub_preservation.md](./13_fixed_output_stub_preservation.md) | fixed output stub 보존(Pass3·Recovery·Reclaim) |
| [14_soft_corridor_atomic_replace.md](./14_soft_corridor_atomic_replace.md) | soft corridor: replacement + atomic replace(§14.3) |
| [15_final_validation_assertion_only.md](./15_final_validation_assertion_only.md) | STEP9 assertion만·새 route/trunk 금지(§15.3) |
| [16_replay_trace_solver_summary_layer.md](./16_replay_trace_solver_summary_layer.md) | Replay/NDJSON/`solver_summary`는 trace 계층 |

## 폴더 이름

장기적으로는 `refactor/` 철자가 자연스럽다. 이미 `refactory`로 경로가 잡혀 있으면 **이동 비용 대비** 문서만 두고 네이밍은 플랜에서 결정한다.

**정본(알고리즘 조각):** `documents/Algorithm/mining_solver_cursor_sessions/`  
**관련 플랜 예시:** `documents/plans/`
