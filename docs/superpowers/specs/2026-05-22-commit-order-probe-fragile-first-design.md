# Commit Order — Probe-Fragile-First (Tier 1.1 / C′) — Design Spec

**Status:** Implemented 2026-05-22  
**Owner:** solver-runtime-pipeline  
**Date:** 2026-05-22  
**Track:** C′ (commit survivability via **order only**) — not selection score, not variant swap, not capacity-96  
**Parent:** [`2026-05-22-phase-i-commit-survivability-design.md`](2026-05-22-phase-i-commit-survivability-design.md) (Tier 1 — no reference-run gain)  
**Related:** [`2026-05-22-deferred-commit-retry-design.md`](2026-05-22-deferred-commit-retry-design.md), [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md), `commit_order_diversity.py`

## Problem (reference run after Tier 1)

```text
selected 24 → commit 20 + route_probe_failed 4
deferred_retry_recovered 0/4
selection_skipped_inlet_on_shared_transport_count 0
validation_passed true
```

Tier 1 (inlet mirror + weak shared-path score + probe budget parity) did not move `confirmed_count`. Evidence points to **commit order under live route-domain congestion**:

- Same 24 candidates are selected; four fail on **commit reprobe**.
- Deferred retry after 20 confirms **never** recovers them (later domain is stricter, not looser).
- Inlet / footprint / validation remain clean.

**Hypothesis (C′):** The four failures are **probe-fragile** bundles that must commit **before** stable/cheap bundles consume corridor capacity. Current `diversify_commit_order` **round-robin interleave** tends to push corridor-heavy / same-bucket runs **later**, worsening order-dependent `ROUTE_PROBE_FAILED`.

## Success criteria (T1.1-GATE)

| Gate | Requirement |
|------|-------------|
| G1 | `len(ordered_candidate_ids)` after selection unchanged (24 on reference when budget allows) |
| G2 | `confirmed_count` ≥ **22** on reference asteroid (stretch: **24**) |
| G3 | `commit_route_probe_failed_count` (final) ≤ **2** (stretch: **0**) |
| G4 | `validation_passed` stays true |
| G5 | `occupied_cell_conflict == 0`, `commit_inlet_on_shared_transport_count == 0` |
| G6 | Unit tests for order policy green; existing commit/validation tests green |

**Non-goals:** Selection score retune, variant swap, second deferred retry round, `target_miner_bundle_count` / capacity planner, rollback/reclaim, GA.

## Approved approach: probe-fragile-first total order

Replace pipeline default post-selection ordering:

```text
SelectedCandidatePlan (Phase I)
  → apply_commit_order_policy(PROBE_FRAGILE_FIRST)   # NEW default in v0 pipeline
  → commit_selected_candidates (Phase J + deferred retry unchanged)
```

**Multiset invariant:** commit plan is a **permutation** of `plan.ordered_candidate_ids` — same 24 IDs, no add/remove.

### Sort key (deterministic, generation-time probe only)

Use **only** Phase H snapshot fields (never commit reprobe results — same rule as fitness):

```python
def commit_survivability_sort_key(
    candidate: GeneCandidate,
    *,
    shared_path_pressure_proxy: int,
) -> tuple[int, int, int, str]:
    probe = candidate.route_probe_result
    return (
        -probe.expanded_nodes,
        -probe.cost,
        -shared_path_pressure_proxy,
        candidate.candidate_id,
    )
```

`max(plan, key=...)` → **probe-fragile first** (high `expanded_nodes`, high `cost`, high shared-path proxy).

**Rationale vs “stable-first”:** committing cheap/easy bundles first consumes corridor; fragile bundles then fail reprobe. This run’s `0/4` deferred recovery supports **fragile-first**, not stable-first.

### Shared-path pressure proxy (commit-order static)

At ordering time, for each candidate `c` in the 24-set:

```text
others_union = ⋃ planned_route_cells(x) for x in plan, x ≠ c
shared_path_pressure_proxy(c) = |planned_route_cells(c) ∩ others_union|
```

- `planned_route_cells` = `frozenset(normalize_probe_path(c, c.route_probe_result.path))` from [`route_path_normalization.py`](../../../django_apps/asteroid_lab/optimization/route_path_normalization.py).
- Predictive only; does **not** read `CommitSurvivabilityMetrics` or commit outcomes.

Tie-break: `candidate_id` lexicographic (existing deterministic pattern).

## Policy enum and API

### `CommitOrderPolicy` (`enums.py` — StrEnum, no free strings)

```python
class CommitOrderPolicy(StrEnum):
    ROUND_ROBIN_DIVERSITY = "round_robin_diversity"  # legacy diversify_commit_order
    PROBE_FRAGILE_FIRST = "probe_fragile_first"
```

### `commit_order_diversity.py` (extend module)

| Function | Behavior |
|----------|----------|
| `diversify_commit_order(...)` | **Unchanged** — round-robin across goal/corridor/anchor buckets |
| `order_probe_fragile_first(plan, candidates_by_id)` | **New** — total sort by `commit_survivability_sort_key` |
| `apply_commit_order_policy(policy, plan, candidates_by_id)` | Dispatch; default for Solver button v0 = `PROBE_FRAGILE_FIRST` |

Pipeline change (`solver_runtime_pipeline.py`):

```python
commit_plan = apply_commit_order_policy(
    CommitOrderPolicy.PROBE_FRAGILE_FIRST,
    plan,
    candidates_by_id,
)
```

Optional later: run-config key — **out of scope** for T1.1 (fixed policy in pipeline).

## Observability (`solver_summary`)

| Key | Type | Meaning |
|-----|------|---------|
| `commit_order_policy` | str (enum `.value`) | e.g. `probe_fragile_first` |
| `commit_failed_candidate_initial_order_positions` | `dict[str, int]` | 0-based index in **selection** plan for each **final** `ROUTE_PROBE_FAILED` skip |
| `commit_failed_candidate_after_order_positions` | `dict[str, int]` | 0-based index in **commit** plan for same IDs |

Populate after commit from `skipped_candidates` + `plan.ordered_candidate_ids` + `commit_plan.ordered_candidate_ids`. Empty dict when no probe failures.

Existing deferred-retry metrics unchanged.

## Architecture

```text
Phase I select (unchanged)
       │
       ▼
apply_commit_order_policy(PROBE_FRAGILE_FIRST)
  sort: -expanded_nodes, -cost, -shared_path_proxy
       │
       ▼
Phase J commit + deferred retry (unchanged)
```

```mermaid
flowchart LR
  S[Selection plan 24 ids]
  O[order_probe_fragile_first]
  C[commit_selected_candidates]
  S --> O --> C
```

## Alternatives considered

| Option | Verdict |
|--------|---------|
| **A — probe-fragile-first total sort** (approved) | Minimal diff; targets order-dependent reprobe; preserves 24-set |
| **B — keep round-robin, only swap failed-four earlier** | Needs failure foresight; not deterministic at order time |
| **C — stable-first (low cost first)** | Contradicts 0/4 deferred recovery evidence on reference run |
| **D — score scale (Tier 1.2)** | Deferred until T1.1-GATE measured |

## Forbidden (T1.1)

- Changing Phase I score weights or greedy selection.
- Variant / anchor swap at selection.
- `deferred_retry_rounds > 1` or retrying non-`ROUTE_PROBE_FAILED` reasons.
- Using commit reprobe `expanded_nodes` in the sort key.
- Rolling back confirmed placements.

## Testing (TDD vertical slices)

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_order_probe_fragile_first_sorts_high_expanded_nodes_first` | Two IDs, same goal; higher `expanded_nodes` earlier in commit plan |
| 2 | `test_order_probe_fragile_first_preserves_multiset` | Sorted plan is permutation of input |
| 3 | `test_order_probe_fragile_first_shared_path_proxy_tiebreak` | Equal nodes/cost; higher overlap with others orders earlier |
| 4 | `test_apply_commit_order_policy_round_robin_unchanged` | Legacy policy matches existing `diversify_commit_order` behavior |
| 5 | `test_solver_summary_includes_commit_order_observability` | Patch/small run: keys present; policy value correct |
| 6 | Regression | `test_incremental_commit.py`, `test_commit_order_diversity.py` (round-robin tests still call `diversify_commit_order` directly) |

```bash
python -m pytest tests/unit/asteroid_lab/test_commit_order_diversity.py tests/unit/asteroid_lab/test_incremental_commit.py tests/unit/asteroid_lab/test_solver_runtime_pipeline.py
python -m ruff check django_apps/asteroid_lab/optimization/commit_order_diversity.py django_apps/asteroid_lab/optimization/enums.py django_apps/asteroid_lab/services/solver_runtime_pipeline.py
```

Manual: re-run reference asteroid Solver → T1.1-GATE.

## Implementation order

1. `CommitOrderPolicy` enum + tests for values.
2. `shared_path_pressure_proxy` helper + `order_probe_fragile_first` (RED → GREEN).
3. `apply_commit_order_policy` dispatch.
4. Pipeline default `PROBE_FRAGILE_FIRST` + summary observability.
5. Doc sync: `phase_j_incremental_commit.md` (commit order subsection), link from Tier 1 spec.

## Doc sync

- [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md) — document policies; v0 pipeline default `probe_fragile_first`; retain `round_robin_diversity` for tests/legacy.
- [`2026-05-22-phase-i-commit-survivability-design.md`](2026-05-22-phase-i-commit-survivability-design.md) — add “Tier 1.1 follow-up” pointer.

## Risks

| Risk | Mitigation |
|------|------------|
| Fragile-first starves later stable bundles | T1.1-GATE on reference; multiset still 24 — only order changes |
| `expanded_nodes` noisy across genes | Tie-breakers: cost, shared-path proxy, `candidate_id` |
| T1.1-GATE still 20/4 | Proceed to Tier 1.2 score scale or Tier 2 variant/Gate C per roadmap |
| `assumption:` four failures are order-not-reachability-in-pool | If G2/G3 fail, log positions prove (or disprove) order hypothesis |

## Rollback

Set pipeline to `CommitOrderPolicy.ROUND_ROBIN_DIVERSITY` (one-line) to restore pre-T1.1 interleave without touching selection or commit rules.
