# Asteroid Lab — Future Execution Plan (Post Sequence 11)


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

Role: Principal Solver System Architect

---

# Purpose

Completed so far:

```text
Sequence 1A–11B
12C–12E
```

This document fixes subsequent development priorities, scope, prohibitions, and verification criteria at canonical level.

This document is a follow-up plan to extend the following in a long-term maintainable form:

```text
Optimization replay
Evolutionary optimization
Incremental commit
UI replay
Regression stability
```

---

# Current State Summary

Current implementation status:

```text
[x] DTO / topology / route domain
[x] pattern library
[x] candidate + probe
[x] genome / fitness
[x] evolutionary search v0
[x] incremental commit
[x] validation
[x] optimization replay
[x] dual-track replay UI
[x] readonly overlay projection
[x] overlay rendering
[x] POST optimization replay persist
```

Remaining key risks:

```text
- narrow corridor starvation
- replay scale growth
- overlay lifecycle drift
- commit survivability under congestion
- route fragility after reservation accumulation
- full-repository gate debt
```

---

# Core Principles (maintained)

## 1. Replay is output only

```text
Replay / artifact / metrics / NDJSON
must never become solver input.
```

---

## 2. No implicit replay synchronization

```text
Lab replay
!=
Optimization replay
```

Without explicit policy, the following are prohibited:

```text
- frame index coupling
- autoplay coupling
- timeline ownership merge
```

---

## 3. Placement never bypasses feasibility

Continue to maintain:

```text
candidate generation
+
immediate route feasibility
```

---

## 4. Commit-time probe is authoritative

Candidate-stage reachable is:

```text
not a commit success guarantee
```

Always:

```text
re-probe against latest route_domain snapshot
```

---

# Next Priorities

# Priority 1 — Sequence 10 Completion

**Status update (2026-05-21, realigned to actual tree):** [`asteroid_lab_10_development_sequence.md`](../../Algorithm/asteroid_lab_10_development_sequence.md) §10B — **contract and observability goals documented only; implementation and fixtures not started**. Paths below are **design/planning only** and may not exist in the current repository: `tests/fixtures/shapez_asteroid/`, `tests/unit/shapez_asteroid/`. **Actual v0 verification** is in `tests/unit/asteroid_lab/`. **10B narrow corridor / survivability regression pack, JSON golden, replay_long envelope** are follow-up work. **Lab unified replay** truncation pairing is runtime **frame `metrics` → track `metrics`**; fixture envelope top-level `truncation_reason` is **golden-only**. Do not read this as "Sequence 10 fully complete".

## Goal

Establish a regression validation foundation for:

```text
corridor / congestion / route fragility
```

---

# Sequence 10A — Narrow Corridor Fixture

## Purpose

In narrow corridor environments, make the following reproducible:

```text
- trunk sharing
- congestion
- unreachable after commit
- route starvation
```

---

## Fixture Requirements

```text
single narrow corridor
multiple extractor competition
mixed transport kinds
existing trunk attachment
protected corridor overlap risk
```

---

## Situations to Include

### Situation 1

```text
candidate probe reachable
→ commit stage unreachable
```

---

### Situation 2

```text
high throughput candidate
blocks future expansion
```

---

### Situation 3

```text
shared corridor pressure
causes rollback
```

---

### Situation 4

```text
shape belt corridor
fluid pipe conflict
```

---

## Tests

```text
test_narrow_corridor_probe_vs_commit_regression
test_shared_corridor_pressure_regression
test_future_expansion_penalty_regression
test_trunk_sharing_penalty_regression
test_transport_kind_corridor_conflict_regression
```

---

## Completion Criteria

```text
[ ] deterministic optimization result
[ ] replay stable across same seed
[ ] congestion regression reproducible
[ ] commit rollback reproducible
```

---

# Sequence 10B — Route Fragility Regression Pack

```text
10B-v0: metrics contract + PenaltyMode — spec only (see asteroid_lab_10 §10B, not implemented)
10B narrow corridor expansion (#14): [ ] planned under tests/unit/asteroid_lab/ or future shapez_asteroid fixtures
10B symmetric dual-goal narrow bridge: [ ] planned
JSON fixture pack (shapez_asteroid/replay/, replay_long/): [ ] planned; fixture envelope ≠ runtime persist
```

> **Implementation cross-reference (2026-05-21):** `CommitSurvivabilityMetrics`, `PenaltyMode`, and `COMMIT_SURVIVABILITY_SUMMARY` exist as **documentation contracts only**. Python DTO, golden, and `summarize_incremental_commit` are not started. **Predictive** penalties are Phase 5; **observed** survivability is replay and post-commit only (solver/GA input forbidden).

## Purpose

Verify that fitness:

```text
route_fragility_penalty
shared_corridor_pressure_penalty
```

connect to actual commit survivability.

---

## Work

```text
[ ] reservation accumulation fixture
[ ] corridor starvation replay fixture
[ ] late-generation unreachable fixture
```

---

## Completion Criteria

```text
[ ] regression reproducible without fragility penalty
[ ] confirm regression reduction when penalty applied
```

---

# Priority 2 — Sequence 11C

# Sequence 11C — Explicit Replay Sync Policy

## Status

```text
optional
not default
```

Current default policy:

```text
no implicit sync
```

maintained.

---

## Conditions to Start This Sequence

Only when the following UX requirements are actually needed:

```text
- coupled playback
- lockstep timeline mode
- jump-to-related-frame
- synchronized scrubber
```

---

## Prohibited

The following must never be auto-connected:

```text
same frame number
same event order
same playback speed
```

---

## Allowed Approach

Must provide:

```text
explicit sync mode
```

as a user toggle.

Example:

```text
[ ] Sync optimization timeline with lab replay
```

---

## Requirements

### Sync ownership

Even in synchronized state:

```text
Lab replay owns map rendering
Optimization replay owns optimization metadata
```

maintained.

---

### One-way sync first

v0 recommendation:

```text
optimization frame
→ optional lab replay jump
```

one-way.

Reverse-direction autoplay coupling prohibited.

---

## Tests

```text
test_explicit_sync_mode_disabled_by_default
test_explicit_sync_mode_does_not_mutate_lab_state_when_disabled
test_explicit_sync_mode_preserves_overlay_ownership
```

---

## Completion Criteria

```text
[ ] sync mode optional
[ ] disabled by default
[ ] no implicit coupling remains
```

---

# Priority 3 — Overlay Lifecycle Stability

Note:

```text
not in current canonical sequence
```

If needed, extend as:

```text
11D
```

---

# Proposed Sequence 11D — Overlay Lifecycle Stability

## Purpose

Ensure overlay replay remains stable under:

```text
large replay
rapid scrub
zoom/pan
DOM rebuild
```

---

## Work

```text
[ ] projection cache
[ ] stale render guard
[ ] replay_truncated HUD
[ ] overlay partial repaint
[ ] transform ownership invariant
```

---

## Core Invariant

```text
Overlay never owns viewport transform.
```

viewport transform owner:

```text
Lab stage only
```

---

## Tests

```text
test_overlay_projection_cache_deterministic
test_overlay_stale_render_guard
test_overlay_transform_ownership
test_overlay_partial_repaint
```

---

## Completion Criteria

```text
[ ] overlay redraw deterministic
[ ] no rapid scrub race
[ ] no zoom drift
[ ] replay_truncated visible
```

---

# Priority 4 — Evolution Search v1

Currently centered on:

```text
mutation-only + repair
```

Next step is:

```text
diversity stabilization
```

---

# Sequence 12A — Diversity Stabilization

## Purpose

Prevent local optimum collapse.

---

## Work

```text
[ ] topology diversity metrics
[ ] rim entropy metrics
[ ] distant mutation scheduler
[ ] population collapse detector
```

---

## Tests

```text
test_population_diversity_survives_long_run
test_forced_distant_mutation_breaks_local_optimum
```

---

## Completion Criteria

```text
[ ] reduced repeated same-topology collapse
[ ] deterministic under same seed
```

---

# Sequence 12B — Commit Survivability Fitness

**Timeline:** **v0.1 (prerequisite)** — Phase 5 `PenaltyMode.CONSERVATIVE` + predictive penalties (candidate domain). **v1+ (this section)** — post-commit survivability estimation (observed metrics forbidden as solver input).

## Purpose

Align fitness **predictive** estimation with actual commit success rate (not a global commit predictor).

---

## Work

```text
[ ] v0.1: conservative fragility/corridor penalties in FitnessBreakdown (Phase 5)
[ ] v1+: post-commit survivability estimation (observability / replay only)
[ ] reservation pressure heuristic
[ ] future expansion survivability scoring
```

---

## Completion Criteria

```text
[ ] reduced reachable-but-uncommittable candidates
```

---

# Priority 5 — Replay Scalability

Currently assumes:

```text
full snapshot replay
```

As active cells grow, need to address:

```text
memory / payload / DOM pressure
```

---

# Sequence 13A — Replay Compression Research

## Purpose

Handle large replay artifacts.

---

## Work

```text
[ ] delta frame prototype
[ ] immutable snapshot reuse
[ ] overlay diff serialization
[ ] binary replay experiment
```

---

## Important

Must not break v0 replay contract.

That is:

```text
serialization optimization
!=
semantic replay mutation
```

---

## Tests

```text
test_compressed_replay_equivalent_to_full_snapshot
test_replay_deterministic_after_compression
```

---

## Completion Criteria

```text
[ ] replay semantic equivalence maintained
[ ] confirm payload reduction
```

---

# Sequence 13B — Lab replay payload attribution (reduction design only)

**Scope:** Lab-only extension of ``measure_json_sections``, duplicate and top-level frame meta key presence in POST regression, sync with ``asteroid_lab_09_replay_debug.md`` "Sequence 13B" and this section. **Payload reduction implementation is 13C.**

## Completion Criteria

```text
[x] Lab replay contribution and duplicate profile measurable via test helper
[x] optimization ``MAX_REPLAY_*`` vs Lab uncapped boundary documented
[x] 13C option ranking, semantic risk, and equivalence test design draft
```

---

# Sequence 13C — Lab replay payload reduction (implementation TBD)

After 13B design and measurement approval: delta, intern, endpoint separation, HTTP compression, etc. in a **separate implementation PR**. When 13C starts, this document and ``asteroid_lab_09`` "13C" section will update execution order.

---

# Priority 6 — Full Repository Quality Gates

**2026-05-17 local verification:** `python -m ruff check .` · `python -m black --check .` · `python -m mypy .` · `python -m pytest` all green (792 tests, no code changes). Reproduction in CI and other environments is separate observation.

Past memo (items left as known debt before merge):

```text
ruff
mypy
black --check
```

---

# Sequence 14A — Repository Gate Cleanup

## Work

```text
[x] full-repository `ruff check .` run and green (2026-05-17 local)
[x] full-repository `black --check .` run and green (same)
[x] full-repository `mypy .` run and green (same)
[x] full-repository `pytest` run and green (792 passed, same; no code changes)
```

> In this sweep the above gates were already green, so **no additional mechanical fix PR body**. Track E501, stub, and format issues in this table again on future drift.

---

## Prohibited

No optimization architecture changes.

This sequence is:

```text
repository hygiene only
```

---

## Completion Criteria

```text
[x] ruff check . green (2026-05-17 local)
[x] black --check . green (2026-05-17 local)
[x] mypy . green (2026-05-17 local)
[x] pytest full suite green (792 passed, same date local)
```

---

# Long-Term Plan (v2+)

The following is after v0/v1.

---

# Sequence 20+ — Advanced Optimization

## Candidates

```text
CP-SAT hybrid refinement
corridor balancing
trunk redundancy scoring
multi-objective Pareto search
advanced reroute planner
```

---

## Prohibited

The following remain prohibited:

```text
cell-level GA
replay-driven algorithm
implicit replay coupling
```

---

# Final Priority Summary

## Immediate

```text
1. Sequence 10A narrow corridor fixture
2. Sequence 10B route fragility regression
```

---

## Optional / Conditional

```text
3. Sequence 11C explicit sync policy
4. Sequence 11D overlay lifecycle stability
```

---

## Mid-term

```text
5. Sequence 12A diversity stabilization
6. Sequence 12B commit survivability fitness
7. Sequence 13A replay scalability — research/measurement phase (13A): ``tests/support/measure_json_sections.py``,
   integration test ``test_post_projects_json_size_attribution_and_optimization_replay_hard_caps``,
   rationale, gaps, and candidate strategies in ``asteroid_lab_09_replay_debug.md`` "Sequence 13A".
   (immediate delta implementation and DTO semantic changes are out of scope)
8. Sequence 13B Lab replay payload attribution — 13A measurement extension (Lab duplicates, top-level frame, ``lab_total_bytes``),
   13B key regression in same integration test, design and 13C roadmap in ``asteroid_lab_09_replay_debug.md`` "Sequence 13B".
   (actual POST payload reduction is 13C)
```

---

## Infrastructure

```text
9. Sequence 14A repository gate cleanup
```

---

# Final Conclusion

The most important thing now is to make the situation where:

```text
route feasibility
!=
commit survivability
```

reproducible and verifiable at regression fixture level.

Therefore the next practical priority is:

```text
narrow corridor
shared corridor pressure
reservation accumulation
```

fixture-based regression strengthening.

Only after that is it safe to proceed to:

```text
explicit replay sync
advanced overlay lifecycle
replay scaling
```
