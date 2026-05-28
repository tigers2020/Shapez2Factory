---
status: CANCELLED
cancelled_date: 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---
# Deferred Commit Retry (Phase J) ??Design Spec

**Status:** Approved 2026-05-22  
**Owner:** solver-runtime-pipeline  
**Date:** 2026-05-22  
**Track:** C (stability / commit survivability) ??**not** capacity-96, not rim packing  
**Related:** [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md), [`2026-05-22-shared-transport-inlet-design.md`](2026-05-22-shared-transport-inlet-design.md), [`open_decisions.md`](../../../documents/Algorithm/solver_runtime/open_decisions.md) OD-3

## Problem

Solver runs show:

```text
selection upper bound: 24 candidates
primary commit confirmed: 20
primary commit ROUTE_PROBE_FAILED: 4
validation_passed: true
run_success: false (capacity target 96 ??out of scope for this spec)
```

`ROUTE_PROBE_FAILED` at commit time is often **order-dependent**: later `route_domain` snapshots block paths that were reachable when the candidate was probed during Phase H, or when earlier commits in the same pass consumed corridor capacity. Re-running the same candidate after other bundles are confirmed can succeed without changing the selected plan.

## Success criteria (C-GATE)

| Gate | Requirement |
|------|-------------|
| C1 | `validation_passed` stays true |
| C2 | `occupied_cell_conflict == 0`, `inlet_on_shared_transport == 0` (unchanged commit rules) |
| C3 | `confirmed_count` ??24 when selection provides 24 non-overlapping footprints |
| C4 | `commit_route_probe_failed_count` (final) < 4 on the reference asteroid run |
| C5 | No rollback of already-CONFIRMED placements |
| C6 | `run_success` may remain false (96 target unchanged) |

## Non-goals (v0)

- Changing `target_miner_bundle_count` or capacity planner (D track)
- Rim packing / smaller-footprint DB policy (B track)
- Multi-pass selection+commit (option 3)
- Phase I inlet mirror (separate spec; may follow after C-GATE)
- Retrying skips other than `ROUTE_PROBE_FAILED` (e.g. inlet, transport conflict)
- GA / evolution

## Approved approach: 1-pass + deferred retry (option 2)

```text
diversify_commit_order(plan)
  ??commit_selected_candidates (primary 1-pass)
  ??deferred retry round (max 1)
```

Deferred retry is **commit survivability only** ??same `SelectedCandidatePlan`, same `candidates_by_id`, no selection optimizer changes.

## Implementation variants considered

| Variant | Idea | Trade-off |
|---------|------|-----------|
| **A ??Queue, record skip after retry** (recommended) | Primary pass queues probe-failed IDs; `skipped_records` only gets final failures | Clean `skipped_by_reason`; recovered IDs never appear as skipped |
| **B ??Record immediately, delete on recovery** | Primary adds `ROUTE_PROBE_FAILED` to `skipped_records`; retry removes entry on success | Audit of primary failure pass; harder metrics / replay |
| **C ??Reorder-only (no retry)** | Tune `diversify_commit_order` only | Smallest diff; may not recover all 4 |

**Recommendation:** **Variant A**.

## DEFERRED_RETRY_V0 contract

```text
ELIGIBLE:
  candidate skipped in primary pass with CommitConflictReason.ROUTE_PROBE_FAILED only

INELIGIBLE:
  OCCUPIED_CELL_CONFLICT, INLET_ON_SHARED_TRANSPORT, TRANSPORT_KIND_CONFLICT,
  HARD_BLOCKED, HARD_PROTECTED, ROUTE_THROUGH_EQUIPMENT, etc.

RETRY:
  max_rounds = 1
  uses latest route_domain (confirmed reservations + committed occupied)
  same max_probe_expansions as primary pass
  same commit-time path normalization (fixed_output_transport prepend/trim)
  same post-probe conflict checks as primary

ORDER:
  subset of plan.ordered_candidate_ids that are still deferred,
  preserving relative order from the commit plan (after diversify_commit_order)

STATE:
  CONFIRMED placements from primary are never rolled back
  ordinal / reservation_id allocation continues monotonically from primary

OUTCOME:
  success ??append to confirmed; update reservations, occupied, route cells, goal_load
  probe fail again ??append SkippedCandidateRecord(ROUTE_PROBE_FAILED)
  probe ok but post-probe conflict ??append with that reason (no second retry in v0)
```

## Architecture

### Refactor (required)

Extract a single internal **commit attempt** primitive from the current loop body:

```text
_attempt_commit_one(
  candidate,
  state: CommitState,  # reservations, occupied sets, goal_load, ordinal, inp, max_expansions
) -> CommitAttemptResult
```

`CommitAttemptResult` is one of:

- `Confirmed(placement, updated_state_slices)`
- `Skipped(reason, probe?)`
- `DeferredProbeFailed(probe?)` ??only used in primary when `reason == ROUTE_PROBE_FAILED` and deferred retry enabled

Primary loop and deferred loop both call `_attempt_commit_one` so probe + conflict behavior stay identical.

### Primary pass

For each `cid` in `plan.ordered_candidate_ids`:

1. If `OCCUPIED_CELL_CONFLICT` ??record skip immediately (not deferred).
2. Run probe + conflicts via `_attempt_commit_one`.
3. If `ROUTE_PROBE_FAILED` ??push `cid` onto `deferred_queue` (do **not** record skip yet).
4. Any other skip reason ??record skip immediately.
5. If confirmed ??apply state updates (existing logic).

### Deferred pass (one round)

If `deferred_queue` empty ??done.

Else iterate `cid` in `deferred_queue` (plan order):

1. Re-check `OCCUPIED_CELL_CONFLICT` (defensive; should not trigger if selection footprint filter holds).
2. Run `_attempt_commit_one` on latest state.
3. Confirmed ??apply state.
4. Any failure ??`_record_skip` (including second `ROUTE_PROBE_FAILED`).

### Pipeline integration

- `commit_selected_candidates(..., deferred_retry_rounds: int = 1)` ??v0 default 1; `0` disables (tests).
- `solver_runtime_pipeline` unchanged call site except optional wiring of `max_probe_expansions` from run config (see optional follow-up).
- `diversify_commit_order` runs **before** commit (unchanged).

## Observability (`solver_summary` / replay)

Add counters (enum-backed keys in summary builder, no free strings):

| Field | Meaning |
|-------|---------|
| `commit_primary_route_probe_failed_count` | probe failures in primary pass (queued when rounds??; immediate skip when rounds=0) |
| `commit_deferred_retry_rounds` | 1 if round ran, else 0 |

Approved refinements (2026-05-22): retry queue = `ROUTE_PROBE_FAILED` only; deferred post-probe conflict records final reason (no second retry); `commit_route_probe_failed_count` remains **final** count.
| `commit_deferred_retry_eligible_count` | len(deferred_queue) after primary |
| `commit_deferred_retry_recovered_count` | confirmed during deferred pass |
| `commit_deferred_retry_still_failed_count` | final `ROUTE_PROBE_FAILED` from deferred pass |

Existing fields:

- `commit_route_probe_failed_count` ??count **final** skips with `route_probe_failed` only.
- `commit_rolled_back_count` ??`len(skipped_candidates)` final.
- `commit_attempt_count` ??still `len(plan.ordered_candidate_ids)` (primary attempts only; deferred reprobes are separate probes counted in `route_probe_count`).

Replay: extend `record_commit_details` payload with deferred retry counters (mirror summary).

## Error handling

- Unknown `candidate_id` in plan ??existing behavior (KeyError / pool missing at validation).
- `deferred_retry_rounds < 0` ??`ValueError` at API boundary.
- Determinism: same plan + pool + inp ??same confirmed set and same skip reasons.

## Testing

| Test | Behavior |
|------|----------|
| `test_deferred_retry_recovers_probe_failed_after_primary_pass` | Two candidates: first fails probe with empty corridor, second confirms and opens path; deferred retry confirms first |
| `test_deferred_retry_does_not_retry_inlet_or_occupied_skips` | Inlet / occupied skips not queued; no recovery |
| `test_deferred_retry_is_deterministic` | Same inputs ??same confirmed ordering |
| `test_deferred_retry_disabled_when_rounds_zero` | Legacy single-pass skip recording |
| Regression | `test_incremental_commit.py` full module |

Integration (optional): pipeline test asserting `commit_deferred_retry_recovered_count` when fixture reproduces order-dependent failure.

## Optional follow-up (same PR if trivial)

Wire `commit_selected_candidates(..., max_probe_expansions=generation_config.route_probe_max_expansions)` from `solver_runtime_pipeline` so commit reprobe budget matches Phase H.

## Documentation sync

- [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md) ??deferred retry subsection
- [`open_decisions.md`](../../../documents/Algorithm/solver_runtime/open_decisions.md) ??OD-3 note: v1.1 partial (deferred retry only, not full reroute)
- Link from [`README.md`](../../../documents/Algorithm/solver_runtime/README.md) open decisions if needed

## Verification

```bash
python -m pytest tests/unit/asteroid_lab/test_incremental_commit.py
python -m ruff check django_apps/asteroid_lab/optimization/commit_best_candidates.py django_apps/asteroid_lab/services/solver_runtime_pipeline.py
```

Reference asteroid: re-run Solver; expect `confirmed_count` 24 and `commit_route_probe_failed_count` 0 when all four failures were order-dependent.

## Implementation order (for writing-plans)

1. Extract `_attempt_commit_one` + `CommitState` (no behavior change) + regression green
2. Primary pass + `deferred_queue` (variant A skip recording)
3. Deferred pass + summary counters
4. Tests + doc sync
5. Manual solver re-run vs C-GATE
