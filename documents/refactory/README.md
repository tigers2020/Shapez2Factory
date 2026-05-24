# Refactoring Document Index

**Mining layout solver** for shapez2Solver — goal-oriented **refactoring/alignment** memos from canonical docs (`documents/Algorithm/mining_solver_cursor_sessions/`), code audits, and architecture reviews. Plan approval and scope confirmation required before implementation.

## Top Epics (Bundles) → Detail Tickets

| Epic | File | Scope | Detail Documents |
|------|------|-------------|----------------|
| A | [control-flow-refactor.md](./control-flow-refactor.md) | §4.3 recovery, orchestrator, attempt separation | 02, [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md), [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md), [epic_a_implementation_scope.md](./epic_a_implementation_scope.md), [epic_a_active_rows.md](./epic_a_active_rows.md) |
| B | [semantic-fields-refactor.md](./semantic-fields-refactor.md) | `recovery_trigger` / `commit_reason` / rollback·reject | 03, 07 |
| C | [corridor-state-machine-refactor.md](./corridor-state-machine-refactor.md) | candidate/soft/hard·atomic replace | 04, 14 |
| D | [trace-layer-isolation.md](./trace-layer-isolation.md) | replay·NDJSON·summary = output layer | 06, 16 |

**Epic A (operations):** Until **A rows are confirmed** in mini-audit §5.3, do **not** open Epic A **code-only PRs**. See [epic_a_implementation_scope.md](./epic_a_implementation_scope.md) for rationale, exceptions, and scope.

**Cursor execution order (YAML sketch):** [cursor_work_phases.md](./cursor_work_phases.md) (Phase 0–4 + Placement FSM notes)

**Phase 0 deliverable (read-only drift matrix):** [phase0_drift_matrix.md](./phase0_drift_matrix.md) — after PR #2 merge, **evidence enrichment** can proceed on branch `audit/phase0-drift-evidence`.

## Reviewer Consensus: Regression Priority (Summary)

Keep canonical direction; revert areas where **implementation drifted** by mixing trace/recovery/replay layers with control flow.

1. **Semantic namespace** — `recovery_trigger` / `commit_reason` / `rollback_reason` / `rejected_reason` / `event_type` (Epic **B**)
2. **Recovery control flow** — §4.3 per-trigger recovery (Epic **A**)
3. **Protected corridor state machine** — §14 (Epic **C**)
4. **PlacementCommitState** — merged seed exception·§9.6 (doc **05**; coordinate order with Epic A/B)
5. **Trace layer isolation** — no read into algorithm inputs (Epic **D**)

## Detail Document List (01–16 + Epic A mini-audit)

| Document | Goal Summary |
|------|-----------|
| [01_canonical_doc_paths.md](./01_canonical_doc_paths.md) | Remove canonical path confusion·index |
| [02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md) | §4.3 per-trigger recovery vs orchestrator simplification alignment |
| [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) | Epic A pre-entry §4.3 vs code first-pass audit table·identifier glossary |
| [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) | **B (MVP exception)** triggers only vs §4.3 fixed table |
| [epic_a_implementation_scope.md](./epic_a_implementation_scope.md) | Epic A **implementation PR** allowed·forbidden·canonical rationale (scope drift prevention) |
| [epic_a_active_rows.md](./epic_a_active_rows.md) | Epic A **current A rows only** (§5.3 snapshot; explicit when 0) |
| [03_recovery_trace_namespaces.md](./03_recovery_trace_namespaces.md) | `recovery_trigger` / `commit_reason` / `rollback_reason` contract |
| [04_protected_corridor_lifecycle.md](./04_protected_corridor_lifecycle.md) | hard/soft/candidate lifecycle·STEP4 summary block |
| [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md) | merged seed `ROUTED_CONFIRMED` exception·§9.6 alignment |
| [06_replay_timeline_frames.md](./06_replay_timeline_frames.md) | `SOLVER_TIMELINE_FRAME_ORDER`·P4 visibility·§16.2 |
| [07_pass3_commit_reason_contract.md](./07_pass3_commit_reason_contract.md) | Pass3 `commit_reason` extension vs §13.5 |
| [08_existing_layout_analysis_immutability.md](./08_existing_layout_analysis_immutability.md) | STEP 0.5 output immutability·DTO conversion |
| [09_pass12_cheap_escape_probe_contract.md](./09_pass12_cheap_escape_probe_contract.md) | Pass1/2 cheap escape·probe must not pollute occupied/route |
| [10_step4_trunk_seed_vs_goal_set.md](./10_step4_trunk_seed_vs_goal_set.md) | Keep trunk seed vs route goal set role separation |
| [11_trunk_load_observation_contract.md](./11_trunk_load_observation_contract.md) | `trunk_load` primary sum observation·keep hard gate unused |
| [12_pass3_lexicographic_priority.md](./12_pass3_lexicographic_priority.md) | Pass3 lexicographic tuple·§10.4·`lexicographic_router` alignment |
| [13_fixed_output_stub_preservation.md](./13_fixed_output_stub_preservation.md) | fixed output stub preservation (Pass3·Recovery·Reclaim) |
| [14_soft_corridor_atomic_replace.md](./14_soft_corridor_atomic_replace.md) | soft corridor: replacement + atomic replace (§14.3) |
| [15_final_validation_assertion_only.md](./15_final_validation_assertion_only.md) | STEP9 assertion only·no new route/trunk (§15.3) |
| [16_replay_trace_solver_summary_layer.md](./16_replay_trace_solver_summary_layer.md) | Replay/NDJSON/`solver_summary` are trace layer |

## Folder Name

Long term `refactor/` spelling is more natural. If path is already `refactory`, **keep documents here** and decide naming in plan based on move cost.

**Canonical (algorithm slices):** `documents/Algorithm/mining_solver_cursor_sessions/`  
**Related plan example:** `documents/plans/`
