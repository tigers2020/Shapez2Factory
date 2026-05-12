# Cursor 작업 순서 (YAML 스케치)

에이전트·인간이 동일한 Phase 순서를 쓰기 위한 스케치다. **플랜 승인 후** 구현에 넣는다.

## Phase 0 — 코드 변경 없는 drift 매트릭스

```yaml
name: Document-aligned solver drift audit
overview: >
  Do not modify code. Compare current implementation against
  documents/Algorithm/mining_solver_cursor_sessions and documents/refactory.
  Produce a drift matrix only.
todos:
  - Find all uses of recovery_trigger, commit_reason, rollback_reason, rejected_reason, event_type.
  - Find all recovery_orchestrator branch return paths and compare with §4.3 trigger table.
  - Find all protected corridor state transitions and classify candidate/soft/hard lifecycle gaps.
  - Find all reads of solver_summary, replay_events, latest.ndjson, or debug trace from algorithm code paths.
  - Find all PlacementCommitState transitions and merged existing seed exceptions.
  - Output file/function/line references and no code changes.
```

## Phase 1 — Semantic field cleanup

```yaml
name: Recovery trace namespace refactor
overview: >
  Align recovery_trigger, commit_reason, rollback_reason, rejected_reason, and event_type with §13.5 and §16.3.
todos:
  - Define enum/constants for recovery triggers.
  - Define enum/constants for successful commit reasons only.
  - Define enum/constants for rollback/reject reasons.
  - Replace any commit_reason misuse with recovery_trigger/event_type/rejected_reason as appropriate.
  - Update tests that asserted old mixed strings.
  - Add regression test: committed=false must not have commit_reason.
```

## Phase 2 — Recovery branch routing

```yaml
name: Recovery control-flow realignment
overview: >
  Restore §4.3 trigger-specific return paths. Recovery is a bounded branch, not a linear STEP.
todos:
  - Encode trigger -> return policy table.
  - Ensure pass3_connectivity_break rolls back Pass3 and returns to STEP 6.
  - Ensure post_reclaim_pass3_connectivity_break rolls back rerun and proceeds to STEP 9 with no extra rerun.
  - Ensure final_validation_failure returns only to STEP 9 revalidation, not STEP 4.
  - Separate cascade_corrective_attempts from total_recovery_attempts.
  - Add tests for each trigger return path.
```

## Phase 3 — Protected corridor FSM

```yaml
name: Protected corridor lifecycle refactor
overview: >
  Implement document-aligned candidate/soft/hard protected corridor lifecycle and atomic replacement constraints.
todos:
  - Model candidate_corridor, soft_protected, hard_protected states explicitly.
  - Ensure candidates are discarded unless committed or replacement-validated.
  - Enforce soft corridor removal only after replacement route is computed and validated.
  - Reject hard_protected removal in Pass3/Reclaim/Recovery.
  - Add trace fields for replacement_search_exhausted and atomic replacement decisions.
  - Add tests for no replacement route, hard protected rejection, and successful atomic soft replace.
```

## Phase 4 — Trace layer isolation

```yaml
name: Trace and NDJSON isolation
overview: >
  Ensure replay_events, solver_summary, and NDJSON are output/debug/report layers only and never primary routing input.
todos:
  - Search algorithm modules for reads of NDJSON/latest/replay_events/solver_summary.
  - Move debug-only readers under scripts or report/debug modules if needed.
  - Add comments/contracts at module boundaries.
  - Add regression test or static guard where practical.
  - Keep logs as validation/audit artifacts only.
```

## Phase 5 — (Epic 별도) Placement FSM

`05_placement_fsm_merged_seed.md` 및 §9.6과 연동. Phase 2–3과 순서 충돌 시 **시몬/플랜**에서 순서 확정.
