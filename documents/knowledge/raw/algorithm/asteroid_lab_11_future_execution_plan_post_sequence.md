# Asteroid Lab — Future Execution Plan (Post Sequence 11)

Role: Principal Solver System Architect

---

# Purpose

**Document baseline (2026-05-18):** Only **Decode → Reconstruction** is considered complete in code. Sequences and features below are **plans·specs**; checklists assume **not started (`[ ]`)** reset state as in [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md).

Scope previously grouped as "complete" in older docs (reference only):

```text
Sequence 1A–11B
12C–12E
13A–13B (replay payload instrumentation·Lab attribution; not implementation)
```

Fixes subsequent development priority·scope·forbidden items·verification conditions at canonical level.

This document is the follow-on plan to extend:

```text
Optimization replay
Evolutionary optimization
Incremental commit
UI replay
Regression stability
```

into a long-term maintainable form.

---

# Current status summary

Implementation checklists in documentation (all reset to not started):

```text
[ ] DTO / topology / route domain
[ ] pattern library
[ ] candidate + probe
[ ] genome / fitness
[ ] evolutionary search v0
[ ] incremental commit
[ ] validation
[ ] optimization replay
[ ] dual-track replay UI
[ ] readonly overlay projection
[ ] overlay rendering
[ ] POST optimization replay persist
```

Remaining core risks:

```text
- narrow corridor starvation
- replay scale growth
- overlay lifecycle drift
- commit survivability under congestion
- route fragility after reservation accumulation
- full-repository gate debt
```

---

# Core principles (maintain)

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

Without explicit policy:

```text
- frame index coupling
- autoplay coupling
- timeline ownership merge
```

are forbidden.

---

## 3. Placement never bypasses feasibility

Maintain:

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

Always re-probe against:

```text
latest route_domain snapshot
```

---

# Next priorities

# Priority 1 — Sequence 10 Completion

**Status note (2026-05-21, reordered per actual tree):** [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) §10B — **contract·observability goals documented only; implementation·fixtures not started**. Paths below are **design·planning** and may not exist in the current repo: `tests/fixtures/shapez_asteroid/`, `tests/unit/shapez_asteroid/`. **Actual v0 verification** is `tests/unit/asteroid_lab/` (e.g. `test_incremental_commit.py`, `test_lab_replay_timeline_payload.py`). **10B narrow corridor / survivability regression pack·JSON golden·replay_long envelope** are follow-on (§10B·Priority 1). **Lab unified replay** truncation pair is runtime **frame `metrics` → track `metrics`** ([`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md)); fixture envelope top-level `truncation_reason` is **golden-only** and not used in persist. Do not read as "Sequence 10 fully complete".

## Goal

```text
corridor / congestion / route fragility
```

Secure regression verification foundation.

---

# Sequence 10A — Narrow Corridor Fixture

## Purpose

In narrow corridor environments, make reproducible:

```text
- trunk sharing
- congestion
- unreachable after commit
- route starvation
```

---

## Fixture requirements

```text
single narrow corridor
multiple extractor competition
mixed transport kinds
existing trunk attachment
protected corridor overlap risk
```

---

## Required scenarios

### Scenario 1

```text
candidate probe reachable
→ commit stage unreachable
```

---

### Scenario 2

```text
high throughput candidate
blocks future expansion
```

---

### Scenario 3

```text
shared corridor pressure
causes rollback
```

---

### Scenario 4

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

## Completion criteria

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

> **Implementation cross-reference (2026-05-21):** `CommitSurvivabilityMetrics`·`PenaltyMode`·`COMMIT_SURVIVABILITY_SUMMARY` exist as **documentation contract only**. Python DTO·golden·`summarize_incremental_commit` not started. **Predictive** `route_fragility_penalty` / `shared_corridor_pressure_penalty` are Phase 5 [`asteroid_lab_05_genome_fitness.md`](asteroid_lab_05_genome_fitness.md); **observed** survivability is replay·post-commit only (forbidden as solver/GA input).

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

## Completion criteria

```text
[ ] regression reproducible without fragility penalty
[ ] regression reduced when penalty applied
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

## Conditions to start this sequence

Only when these UX requirements are actually needed:

```text
- coupled playback
- lockstep timeline mode
- jump-to-related-frame
- synchronized scrubber
```

---

## Forbidden

Never auto-connect:

```text
same frame number
same event order
same playback speed
```

---

## Allowed approach

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

Even in sync state:

```text
Lab replay owns map rendering
Optimization replay owns optimization metadata
```

maintained.

---

### One-way sync preferred

v0 recommendation:

```text
optimization frame
→ optional lab replay jump
```

one-way.

Reverse autoplay coupling forbidden.

---

## Tests

```text
test_explicit_sync_mode_disabled_by_default
test_explicit_sync_mode_does_not_mutate_lab_state_when_disabled
test_explicit_sync_mode_preserves_overlay_ownership
```

---

## Completion criteria

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

Keep overlay replay stable under:

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

## Core invariant

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

## Completion criteria

```text
[ ] overlay redraw deterministic
[ ] no rapid scrub race
[ ] no zoom drift
[ ] replay_truncated visible
```

---

# Priority 4 — Evolution Search v1

Currently:

```text
mutation-only + repair
```

centered.

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

## Completion criteria

```text
[ ] reduced repeated same-topology collapse
[ ] deterministic under same seed
```

---

# Sequence 12B — Commit Survivability Fitness

**Timeline:** **v0.1 (preceding)** — Phase 5 `PenaltyMode.CONSERVATIVE` + predictive `route_fragility_penalty` / `shared_corridor_pressure_penalty` (candidate domain, [`asteroid_lab_05`](asteroid_lab_05_genome_fitness.md)). **v1+ (this section)** — post-commit survivability **estimation** (observed metrics still forbidden as solver input).

## Purpose

Align fitness **predictive** estimates with actual commit success rate (not a global commit predictor).

---

## Work

```text
[ ] v0.1: conservative fragility/corridor penalties in FitnessBreakdown (Phase 5)
[ ] v1+: post-commit survivability estimation (observability / replay only)
[ ] reservation pressure heuristic
[ ] future expansion survivability scoring
```

---

## Completion criteria

```text
[ ] reduced reachable-but-uncommittable candidates
```

---

# Priority 5 — Replay Scalability

Currently:

```text
full snapshot replay
```

assumed.

As active cells grow:

```text
memory / payload / DOM pressure
```

response needed.

**Canonical for post-13C implementation order·strategy distinction·out of scope·verification·exit criteria:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)  
Instrumentation·HAR·13A·13B detailed evidence: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md).

---

# Sequence 13A — POST JSON payload instrumentation·scale study (complete)

## Purpose

**Observe·attribute** large POST response·replay artifact scale (not an implementation reduction stage).

---

## Work

```text
[ ] deterministic top-level JSON section instrumentation (tests/support/measure_json_sections.py)
[ ] optimization replay hard cap regression·HAR evidence documentation (asteroid_lab_09 「Sequence 13A」)
[ ] delta frame prototype — 13E roadmap (after approval)
[ ] immutable snapshot reuse — 13E/13F candidate
[ ] overlay diff serialization — separate optimization track review
[ ] binary replay experiment — deferred (asteroid_lab_13 「Deferred」)
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
test_post_projects_json_size_attribution_and_optimization_replay_hard_caps (integration)
(when reduction implemented later) test_compressed_replay_equivalent_to_full_snapshot
```

---

## Completion criteria

```text
[ ] POST JSON upper bound·section contribution repeatable in tests
[ ] optimization vs Lab cap gap fixed in docs·regression
```

---

# Sequence 13B — Lab replay payload attribution (complete, reduction design only)

**Scope:** ``measure_json_sections`` Lab-only extension, duplicate·top frame meta keys in POST regression, sync ``asteroid_lab_09_replay_debug.md`` 「Sequence 13B」·this section. **Payload reduction runtime implementation is 13C (after approval).**

## Completion criteria

```text
[ ] Lab contribution·duplicate profile measurable via test helper
[ ] optimization ``MAX_REPLAY_*`` vs Lab uncapped boundary documented
[ ] post-13C roadmap canonical: asteroid_lab_13 (preferred first = lazy-load endpoint)
```

---

# Sequence 13C–13G — Replay payload reduction (roadmap; after implementation approval)

**Canonical:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)

- **13C (preferred first):** Full Lab replay **lazy-load endpoint** — lightweight POST, frame semantic equivalence.
- **13D:** UI lazy-load, loading/error, dual-track ownership preservation.
- **13E:** Delta prototype — when lazy-load insufficient, reconstruction equivalence tests required.
- **13F:** Cell interning — after redundancy evidence.
- **13G:** HTTP compression·response policy — transport only, must not replace semantics.

On 13C start, sync ``asteroid_lab_09`` 「Sequence 13」·``asteroid_lab_10`` Sequence 13 table·this document with implementation PR.

---

# Priority 6 — Full Repository Quality Gates

**Archive:** Past observation memo of full-repo lint·type·pytest green in one run. 2026-05-18 doc cleanup did not update pass counts·commands; actual state follows CI·local.

Past memo (known debt before merge):

```text
ruff
mypy
black --check
```

---

# Sequence 14A — Repository Gate Cleanup

## Work

```text
[ ] full repo `ruff check .` run·green
[ ] full repo `black --check .` run·green
[ ] full repo `mypy .` run·green
[ ] full repo `pytest` run·green
```

> Past observation of green gates is archive only. On drift, track E501·stub·format issues again in this table.

---

## Forbidden

No optimization architecture changes.

This sequence is:

```text
repository hygiene only
```

---

## Completion criteria

```text
[ ] ruff check . green
[ ] black --check . green
[ ] mypy . green
[ ] pytest full suite green
```

---

# Long-term plan (v2+)

Following v0/v1.

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

## Forbidden

Still forbidden:

```text
cell-level GA
replay-driven algorithm
implicit replay coupling
```

---

# Final priority summary

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
7. Sequence 13A — complete: instrumentation·HAR·hard cap regression (asteroid_lab_09 「13A」)
8. Sequence 13B — complete: Lab attribution·largest_lab_frames·redundancy (asteroid_lab_09 「13B」)
9. Sequence 13C–13G — roadmap canonical asteroid_lab_13; preferred first = 13C lazy-load endpoint;
   delta·interning·compression after semantic equivalence gates. 13C implementation after explicit approval.
```

---

## Infrastructure

```text
10. Sequence 14A repository gate cleanup
```

---

# Final conclusion

Most important now:

```text
route feasibility
!=
commit survivability
```

Make this reproducible and verifiable at regression fixture level.

Therefore practical next priority is:

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
