# Deferred Commit Retry — PR-3 Bounded Execution Design

**Status:** APPROVED 2026-05-24 — pending implementation  
**Owner:** asteroid-lab / RTTP deferred commit retry  
**Track:** RTTP core — deferred commit retry slice 3 of 4  
**Prerequisite:** PR-2 CLOSED `a5cfca87` (PR #73) — runtime policy wiring  
**Related:** [`2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](2026-05-24-deferred-commit-retry-shadow-pr1-design.md) · [`2026-05-24-deferred-commit-retry-pr2-policy-design.md`](2026-05-24-deferred-commit-retry-pr2-policy-design.md) · [`2026-05-22-deferred-commit-retry-design.md`](2026-05-22-deferred-commit-retry-design.md) (CANCELLED Phase J; execution semantics reference only)

---

## Problem

PR-1/PR-2 record which primary-pass candidates would enter a deferred retry queue (`REPROBE_FAILED` only) but never re-probe or commit them. Order-dependent reprobe failures therefore remain in `CommitResult.conflicts` until LNS, even when a one-round retry on the latest `route_domain` (after other primaries confirm) would succeed.

PR-3 adds **bounded deferred retry execution** behind the existing wire key, without changing PR-2 shadow envelope semantics.

---

## Goal

```text
primary incremental_commit → CommitResult_primary
→ rttp.deferred_commit_retry_shadow (always; primary-based diagnostics)
→ if enabled && !observe_only:
      run_bounded_deferred_retry(...) → CommitResult_merged
      rttp.deferred_commit_retry_execute (execution metrics)
  else:
      CommitResult_merged = CommitResult_primary
→ run_local_lns(CommitResult_merged)
→ validation
```

### Canonical statements (normative)

```text
PR-3 does not change PR-2 shadow envelope semantics.
The shadow step is always appended, including enabled=false empty metrics.
Deferred execution is represented only by rttp.deferred_commit_retry_execute.
```

```text
Deferred retry may remove only recovered eligible REPROBE_FAILED conflicts.
It must not mutate, rewrite, or reinterpret unrelated primary conflicts.
```

```text
The merged CommitResult is the authoritative input to LNS.
LNS must not receive primary_commit_result when deferred execution ran.
```

---

## Non-goals (PR-3)

| Item | Deferred to |
|------|-------------|
| `max_retry_rounds > 1` | Future slice |
| Macro pipeline (`_run_macro_rttp_pipeline`) | Out of scope (v0.1 normal path) |
| Shadow step carrying execution flags (`executed=true`, etc.) | Forbidden — use execute step |
| Skipping shadow step when `enabled=false` | Forbidden — PR-2 choice B preserved |
| Validation repair / replay·NDJSON·`solver_summary` as algorithm input | Forbidden (permanent) |
| Retrying non-`REPROBE_FAILED` conflicts | Forbidden |
| Rolling back primary-confirmed candidates | Forbidden |
| Real-map ops smoke | PR-4 |

---

## Wire contract (execution gate — Approach A)

Stable key unchanged: `SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY = "deferred_retry_shadow"`.

### Config matrix

| `enabled` | `observe_only` | Shadow step | Execute step | `commit_result` for LNS |
|-----------|----------------|-------------|--------------|-------------------------|
| `false` | (ignored) | Always append; empty metrics (`enabled=false`, `candidate_count=0`) | None | `CommitResult_primary` |
| `true` | `true` | Append; eligible-candidate diagnostics | None | `CommitResult_primary` |
| `true` | `false` | Append; same diagnostics as observe-only | Append | `CommitResult_merged` |

```python
should_execute_deferred_retry = (
    config.deferred_retry_shadow.enabled
    and not config.deferred_retry_shadow.observe_only
)
```

`enabled=false` means **shadow candidate scan disabled**, not omission of the shadow step envelope.

### Mapper change (atomic with executor)

PR-2 rejects `observe_only: false` at parse time. PR-3 **lifts** that fail-closed **only in the same change** that wires `run_bounded_deferred_retry` and `rttp.deferred_commit_retry_execute`.

| Input | Result |
|-------|--------|
| `observe_only: false` + executor present | Parsed; execution allowed when `enabled=true` |
| `observe_only: false` without executor wiring | Must remain fail-closed (do not merge parser-only) |
| Other PR-2 parse rules | Unchanged (strict bool, no string coercion, etc.) |

---

## Architecture (Approach 1)

### Components

| Unit | Path | Responsibility |
|------|------|----------------|
| Shared commit primitive | `optimization/commit/incremental_commit.py` | `_attempt_commit_one(...)` — single probe + conflict check path |
| Bounded executor | `optimization/commit/deferred_retry_execute.py` (new) | `run_bounded_deferred_retry(...)` → `DeferredRetryExecuteResult` |
| Shadow (unchanged) | `optimization/commit/deferred_retry_shadow.py` | Primary-only diagnostics |
| Pipeline orchestration | `optimization/pipeline.py` | Shadow always → execute conditional → LNS on merged |
| Step ids / events | `rttp_solver_summary.py`, `replay/event_types.py` | `RTTP_DEFERRED_COMMIT_RETRY_EXECUTE` |

PR-3 does **not** fold execution into `incremental_commit(..., deferred_rounds=1)` (Approach 2 rejected: shadow must stay primary-only; large test churn).

PR-3 does **not** duplicate commit logic without extraction (Approach 3 rejected: B-CS1 drift risk).

### Pipeline sequence

```text
primary_commit_result = incremental_commit(...)
_append_deferred_retry_shadow_step(primary_commit_result, ...)  # always

if should_execute_deferred_retry:
    execute_result = run_bounded_deferred_retry(
        primary_commit_result=primary_commit_result,
        commit_order=genome.commit_order,
        candidates_by_id=...,
        inp=..., skeleton=..., config=...,
    )
    commit_result = execute_result.merged_commit_result
    _append_deferred_retry_execute_step(execute_result, ...)
else:
    commit_result = primary_commit_result

if commit_result.conflicts:
    run_local_lns(..., commit_result, ...)
```

---

## Execution semantics (v0)

### Eligibility

Same rules as PR-1 shadow builder:

```text
eligible iff:
  row in primary_commit_result.conflicts
  AND reason == REPROBE_FAILED
  AND candidate_id in genome.commit_order
  AND candidate exists in candidates_by_id
```

Queue ordering: `original_commit_order` ascending, then `candidate_id` (deterministic).

Apply `max_candidates` cap after sort (from `DeferredRetryShadowConfig`).

### Retry pass (one round)

1. Reconstruct `CommitDomainState` from **primary successful commits only** (no rollback of primary-confirmed ids).
2. Iterate eligible queue once in sorted order.
3. For each candidate, call `_attempt_commit_one(..., max_expansions=config.route_probe_max_expansions)`.
4. On confirm: apply state updates; record `recovered_candidate_ids`.
5. On any failure: record final conflict for that attempt; **do not re-queue** in v0.
6. Build `CommitResult_merged` (see below).

`max_retry_rounds` is recorded in config; v0 executor runs **at most one round** regardless of values `> 1` (future slice may honor higher values).

### `CommitResult_merged`

**`committed_ids`** — global genome order:

```text
committed_ids =
  all candidate_ids committed in primary pass
  plus candidate_ids recovered in deferred retry
  sorted by index in genome.commit_order (ascending)
```

Do not append recovered ids after primary ids when genome order places a recovered candidate between primary commits.

**`conflicts`** — row-precise removal:

```text
conflicts =
  primary_commit_result.conflicts
  excluding only eligible REPROBE_FAILED conflict rows
  whose candidate_id was recovered by deferred retry
```

Plus any **new** conflict rows from deferred attempts that failed (including `REPROBE_FAILED` again or a different `CommitConflictReason`).

Deferred retry **must not** remove, rewrite, or reinterpret unrelated primary conflicts (non-eligible reasons, ineligible candidates, or eligible rows that were not recovered).

**`reserved_route_cells` / `domain_version`** — derived from final commit domain state after primary replay + successful retry confirmations (same rebuild rules as `incremental_commit`).

### Shadow vs execute data sources

| Step | Commit input |
|------|----------------|
| `rttp.deferred_commit_retry_shadow` | `CommitResult_primary` only |
| `rttp.deferred_commit_retry_execute` | `DeferredRetryExecuteResult` metrics only |
| LNS (when execution ran) | `CommitResult_merged` only |

---

## Invariants (PR-3)

| ID | Invariant |
|----|-----------|
| INV-PR3-01 | Eligible targets: `REPROBE_FAILED` only |
| INV-PR3-02 | Primary-confirmed candidates never rolled back |
| INV-PR3-03 | At most one deferred round; no re-queue of failures inside the round |
| INV-PR3-04 | `observe_only=true` or `enabled=false`: byte/contract parity with PR-2 for commit, LNS, validation, genome |
| INV-PR3-05 | Shadow step always appended; metrics reflect primary pass only |
| INV-PR3-06 | Execution observability only on `rttp.deferred_commit_retry_execute` |
| INV-PR3-07 | No replay / `solver_summary` / NDJSON as config or queue input |
| INV-PR3-08 | `route_domain` updates via existing rebuild pattern; no alternate snapshot owner |
| INV-PR3-09 | Merged conflicts: only recovered eligible `REPROBE_FAILED` rows dropped from primary set |

---

## Observability — execute step

### Step id and event type

```python
RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE = "rttp.deferred_commit_retry_execute"
EVENT_TYPE_RTTP_DEFERRED_COMMIT_RETRY_EXECUTE = "rttp.deferred_commit_retry_execute"
```

Insert **after** shadow, **before** LNS. Step `passed=True` in v0 (diagnostic; does not gate `validation_passed`).

### Metrics (required)

| Key | Definition |
|-----|------------|
| `deferred_retry_rounds_executed` | `1` if round ran, else `0` |
| `deferred_retry_eligible_count` | Eligible queue length after cap |
| `deferred_retry_recovered_count` | `len(recovered_candidate_ids)` |
| `deferred_retry_still_failed_count` | `deferred_retry_attempted_count - deferred_retry_recovered_count` |
| `recovered_candidate_ids` | Deterministic list |

### Metrics (recommended — PR-4 smoke/debug)

| Key | Definition |
|-----|------------|
| `deferred_retry_attempted_count` | Eligible candidates processed in the round |
| `deferred_retry_failed_reason_counts` | Map `CommitConflictReason.value` → count for failed attempts in the round |

`deferred_retry_still_failed_count` is **not** defined as “still `REPROBE_FAILED`” — failure reason may change on retry.

---

## Testing

### Preserve (PR-2)

- `test_disabled_shadow_step_present_with_empty_metrics`
- `test_disabled_shadow_does_not_change_commit_or_validation`

### Add (PR-3)

| Test | Assert |
|------|--------|
| `test_disabled_shadow_does_not_append_execute_step` | No execute step when `enabled=false` |
| `test_observe_only_true_does_not_append_execute_step` | No execute step when `observe_only=true` |
| `test_observe_only_false_appends_execute_step_after_shadow` | Execute step index > shadow index |
| `test_deferred_retry_recovers_eligible_candidate_when_retry_succeeds` | Merge path when retry attempt confirms (may use monkeypatch) |
| `test_deferred_retry_narrow_corridor_second_still_fails_after_retry` | B-CS1 geometry: second remains `reprobe_failed`; `still_failed_count=1` |
| `test_deferred_retry_does_not_retry_inlet_or_overlap` | Non-eligible stays in conflicts |
| `test_deferred_retry_is_deterministic` | Same inputs → same merged result |
| `test_merged_committed_ids_follow_genome_order` | Recovered id between primaries sorts by `commit_order` |
| `test_lns_receives_merged_not_primary_when_execution_ran` | Mock/spy: LNS `commit_result` is merged |

### Verification commands

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
python -m ruff check django_apps/asteroid_lab/optimization/commit/ django_apps/asteroid_lab/optimization/pipeline.py
python -m black --check django_apps/asteroid_lab/optimization/commit/ django_apps/asteroid_lab/optimization/pipeline.py
```

---

## File map (implementation hint)

| Action | Path |
|--------|------|
| Modify | `incremental_commit.py` — extract `_attempt_commit_one` |
| Create | `deferred_retry_execute.py`, contract DTO `DeferredRetryExecuteResult` |
| Modify | `pipeline.py`, `solver_runtime_entry.py` (mapper lift, atomic) |
| Modify | `rttp_solver_summary.py`, `replay/event_types.py` |
| Create | `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py` |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` (on close) |

---

## Follow-on

| PR | Scope |
|----|--------|
| PR-4 | Real-map regression / ops smoke (`run_solver` slug, execute metrics on trunk) |
