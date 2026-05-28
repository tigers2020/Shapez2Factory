# PR-2d — Throughput-Aware Placement Goals & Shortfall Attribution — Design Spec

**Date:** 2026-05-24  
**Status:** Approved for implementation planning (2026-05-24)  
**Depends on:** PR-1 `MiningExtractionRule` · PR-2a `reconstruction_capacity` · PR-2b `actual_committed_output_per_min` · PR-2c `throughput_target_percent` + budget fields  
**Parent:** [`2026-05-24-throughput-target-percent-pr2c-design.md`](2026-05-24-throughput-target-percent-pr2c-design.md) · [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md)  
**North Star:** Route-feasible committed throughput optimizer (not “place many miners” heuristic)

---

## 1. Problem

Throughput target % is measured and displayed (PR-2c), but RTTP placement selection remains capped by `skeleton.capacity_goals`.

This creates a policy mismatch:

- Reconstruction upper bound may imply a much larger throughput budget.
- The user-selected target may require multiple committed bundles.
- Greedy-regret selection may still receive `goal_count = 1`.
- Validation may pass because topology is valid, while throughput budget is far below target.

Therefore, the solver can be **topologically correct** but **throughput-budget incorrect**.

**Observed regression (ops):** 32 mineable cells, 127 normal candidates, `capacity_goals: 1` → `confirmed_count: 1`, `actual: 120/min`, `target` (10%): `1536/min`. Commit and validation succeed; budget fails due to selection budget, not probe/generation failure.

---

## 2. Success definition

### Primary (user-facing pass)

```text
throughput_budget_satisfied == true
actual_committed_output_per_min >= target_throughput_per_min
```

Equivalently: PR-2c `evaluate_throughput_budget(satisfied=True)` after route-confirmed commits.

### Fail-but-correct (partial route-feasible result)

```text
validation_passed == true
throughput_budget_satisfied == false
actual_committed_output_per_min < target_throughput_per_min
throughput_shortfall_reason is explicit (enum, not free-form)
```

The run must **not** present capacity/throughput success via aliased HUD fields.

### Intermediate regression (dev smoke only — not user pass)

- `confirmed_count >= 2` on the reference slug after PR-2d wiring — useful to detect “still capped at 1” regressions; **does not** substitute for primary pass when `actual < target`.

### Lower-bound heuristic (supporting — not pass definition)

- `placement_goal_count >= skeleton.capacity_goals` when target implies more bundles than skeleton floor.
- Optional: `placement_goal_count >= ceil(mineable_cell_count / SHAPE_PLATFORMS_PER_GOAL)` for shape belt maps — informs caps, not pass/fail alone.

---

## 3. Non-goals

- Do not treat reconstruction max as committed throughput.
- Do not use replay, NDJSON, prior `solver_summary`, or CLR/reflection as algorithm input.
- Do not let validation invent routes, mutate placement, or repair topology.
- Do not redefine `validation_passed` as throughput satisfaction.
- Do not replace incremental commit re-probe or change commit order semantics beyond **how many** candidates selection may pick.
- Do not install Space Belt / Pipe transport grids (deferred track).
- Full GA / macro unpause — out of scope.

---

## 4. Architecture

### Layering

| Layer | Module (proposed) | Responsibility |
|-------|-------------------|----------------|
| Pure policy | `django_apps/asteroid_lab/services/placement_goal.py` | `bundles_needed_for_target`, cap computation, `placement_goal_count`, post-run `throughput_shortfall_reason` |
| Selection | `optimization/selection/greedy_regret.py` | Accept explicit `goal_count`; stop using only `skeleton.capacity_goals` when target-aware run |
| Pipeline | `optimization/pipeline.py` | After candidate pool: compute caps + `placement_goal_count`; pass into `select_genome` / macro path |
| Runtime | `services/solver_runtime_entry.py` | Parse `throughput_target_percent` + `reconstruction_capacity`; pass `PlacementGoalContext` into pipeline config |
| Summary | `optimization/rttp_solver_summary.py` | Decouple `capacity_satisfied` / `placement_capacity_satisfied` from `validation_passed`; emit shortfall reason + goal metrics |

### Data flow

```text
reconstruction_capacity + throughput_target_percent (config)
  → target_throughput_per_min (reuse PR-2c)
  → best_bundle_throughput_per_min from normal pool + MiningExtractionRule
  → bundles_needed_for_target = ceil(target / best_bundle)
  → caps (route-feasible, anchor, configured max)
  → placement_goal_count = min(caps, max(skeleton.capacity_goals, bundles_needed))
  → select_genome(..., goal_count=placement_goal_count)
  → incremental_commit (unchanged semantics)
  → actual_committed_output_per_min (PR-2b)
  → throughput budget eval (PR-2c)
  → if unsatisfied: throughput_shortfall_reason (post-hoc attribution)
```

### Core formulas

```python
best_bundle_throughput_per_min = max(
    output_per_min(rule, c.throughput_factor)
    for c in normal_candidates
    if c.reachable
)

bundles_needed_for_target = ceil(
    target_throughput_per_min / best_bundle_throughput_per_min
)  # Decimal-safe; 0 if best_bundle == 0

placement_goal_count = min(
    route_feasible_candidate_cap,
    non_overlapping_anchor_cap,
    configured_max_placement_goal,
    max(skeleton.capacity_goals, bundles_needed_for_target),
)
```

**Reference slug (10%):** `target = 1536`, `best_bundle = 120` (factor 4) → `bundles_needed_for_target = 13`.

For the reference slug at 10%, `bundles_needed_for_target = 13`. With the default `configured_max_placement_goal = 32`, the configured cap does **not** bind. If `route_feasible_candidate_cap >= 13` and `non_overlapping_anchor_cap >= 13`, then:

```text
placement_goal_count = min(127, anchor_cap, 32, max(1, 13)) = 13
```

`32` is a runaway-prevention ceiling, not the requested goal for this slug. If either route or anchor cap is `< 13`, `placement_goal_count` is lower and primary pass may fail with an explicit cap reason.

**Fixture note:** If the normal pool contains reachable factor-16 bundles, `best_bundle_throughput_per_min` is `480` and `bundles_needed_for_target = 4`. Regression fixtures must pin reachable factors (observed ops regression: factor-4 commit at `120/min`).

### Cap definitions (v0.1)

| Cap | Definition |
|-----|------------|
| `route_feasible_candidate_cap` | Count of `normal_candidates` with `reachable is True` (pool already excludes generation-time unreachable). |
| `non_overlapping_anchor_cap` | Count of distinct `anchor_coord` among deduped reachable normals — **optimistic upper bound** (does not prove pairwise `occupied_cells` disjoint). Document in summary; tighten in v0.1.1 if needed. |
| `configured_max_placement_goal` | Run config `max_placement_goal_count` (integer, default **32**, valid **1..128**). **Fail-closed parse** — invalid type/range → HTTP 400 / `CommandError`; **no silent clamp**. Prevents runaway selection on huge pools. |
| `skeleton.capacity_goals` | Existing CANON floor from `skeleton_builder._capacity_goals` — never **reduced** by target policy. |

### Selection change

`select_genome` today:

```python
goal_count = max(0, skeleton.capacity_goals)
```

PR-2d:

```python
goal_count = placement_goal_count  # computed upstream; 0 allowed → empty genome
```

Greedy-regret **scoring weights unchanged** in PR-2d (still favors `throughput_factor`, rim alignment, fragmentation). PR-2d.1 may add target-shortfall term to `_base_score` if needed after cap lift.

Macro pipeline: same `placement_goal_count` passed to `select_macro_genome` (or macro-specific cap if macro pool smaller — document in plan).

---

## 5. Shortfall attribution

### Enum (required — no free-form strings)

```python
class ThroughputShortfallReason(StrEnum):
    SATISFIED = "satisfied"  # only when budget satisfied; omit or map in summary
    ROUTE_FEASIBLE_CANDIDATE_CAP = "route_feasible_candidate_cap"
    NON_OVERLAPPING_ANCHOR_CAP = "non_overlapping_anchor_cap"
    COMMIT_CONFLICT_CAP = "commit_conflict_cap"
    SELECTION_GOAL_CAP = "selection_goal_cap"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"
    BEST_BUNDLE_ZERO = "best_bundle_zero"
    NO_ACTUAL_OUTPUT = "no_actual_output"
```

### Post-run attribution (read-only, after commit)

Priority when `throughput_budget_satisfied is False` (evaluate in order; first match wins):

1. **Impossible input / pool:** `best_bundle_throughput_per_min == 0` → `best_bundle_zero`; `normal_count == 0` or `route_feasible_candidate_cap == 0` → `candidate_pool_exhausted`
2. **Selection cap** (selection did not reach `bundles_needed_for_target` because `placement_goal_count` or pool stopped early):
   - `len(genome.commit_order) < bundles_needed_for_target` → cap-specific if `placement_goal_count < bundles_needed_for_target`:
     - `placement_goal_count == route_feasible_candidate_cap` → `route_feasible_candidate_cap`
     - `placement_goal_count == non_overlapping_anchor_cap` → `non_overlapping_anchor_cap`
     - `placement_goal_count == configured_max_placement_goal` → `selection_goal_cap`
     - else → `selection_goal_cap`
   - `len(genome.commit_order) < placement_goal_count` (greedy pool exhausted) → `candidate_pool_exhausted`
3. **Commit conflict** (selection reached `placement_goal_count` but commit lost bundles): `len(genome.commit_order) >= placement_goal_count` and (`len(committed_ids) < len(genome.commit_order)` or `conflict_count > 0`) → `commit_conflict_cap`
4. **Throughput still short** at full selection+commit count: `len(committed_ids) >= len(genome.commit_order)` and `len(genome.commit_order) >= placement_goal_count` and `actual < target` → `selection_goal_cap` (per-bundle throughput / route domain insufficient)

Persist on `solver_summary`:

```json
"throughput_goal": {
  "placement_goal_count": 13,
  "bundles_needed_for_target": 13,
  "best_bundle_throughput_per_min": "120.0000",
  "route_feasible_candidate_cap": 127,
  "non_overlapping_anchor_cap": 42,
  "configured_max_placement_goal": 32,
  "skeleton_capacity_goals": 1,
  "selected_count": 13,
  "committed_count": 8,
  "throughput_shortfall_reason": "commit_conflict_cap"
}
```

When unsatisfied: keep PR-2c `issue_codes` entry `throughput_target_shortfall`; add `issue_details: [{ "code": "throughput_target_shortfall", "throughput_shortfall_reason": "<enum>" }]`.

---

## 6. Summary / HUD honesty (PR-2d scope)

`capacity_satisfied` and `placement_capacity_satisfied` are **deprecated compatibility fields**. They must **not** drive user-facing green/pass UI. The only user-facing throughput pass field is `throughput_budget_satisfied`.

| Field | PR-2d behavior |
|-------|----------------|
| `capacity_satisfied` | Deprecated. Emit `false` when `throughput_budget_satisfied` is false; may mirror `validation_passed` for legacy readers only — **never** true solely because validation passed. |
| `placement_capacity_satisfied` | Dev-only metric: `len(committed_ids) >= min(placement_goal_count, bundles_needed_for_target)` when `throughput_goal` present; else `false`. Not user-facing pass. |
| `target_miner_bundle_count` | `len(commit_order)` — unchanged |
| `throughput_budget_satisfied` | PR-2c truth — **only** user-facing budget pass |

Lab UI (`asteroid_miner_layout_lab.js`): success/chip green uses `throughput_budget_satisfied` for budget card; show `throughput_goal` rows in Detail C; do not treat `capacity_satisfied` as pass.

---

## 7. Config keys

| Key | Type | Default | Validation |
|-----|------|---------|------------|
| `throughput_target_percent` | int | 80 | PR-2c (10..80) |
| `max_placement_goal_count` | int | 32 | Integer **1..128**; invalid type or out of range → fail-closed error (no clamp to 32/128) |

**Forbidden:** reading goal caps from prior `solver_summary` when building a new run; silent clamp of invalid `max_placement_goal_count`.

---

## 8. Tests (required)

| Module | Cases |
|--------|-------|
| `test_placement_goal.py` | bundles_needed ceil; min caps; slug fixture → goal > 1 when target 10%; best_bundle_zero |
| `test_rttp_greedy_regret.py` | `goal_count=13` selects up to 13 non-overlapping when pool allows |
| `test_rttp_pipeline.py` or integration | reference slug: `placement_goal_count >= bundles_needed` cap binding; committed may be < selected |
| `test_throughput_shortfall.py` | attribution priority for conflict vs cap |
| `test_rttp_solver_summary.py` | `capacity_satisfied` not true when only validation passed and budget false |
| `test_solver_run_lab_summary.py` | nested `throughput_goal` DTO |

**Primary acceptance (manual / ops):** same slug as ops, `throughput_target_percent=10` → if route-feasible caps allow, `actual >= 1536` and `throughput_budget_satisfied`; else fail with explicit `throughput_shortfall_reason` and honest HUD.

---

## 9. PR split

| PR | Delivers |
|----|----------|
| PR-2c | Target % measurement + budget fields (no selection change) |
| **PR-2d** | `placement_goal_count`, selection cap lift, shortfall enum + summary, HUD honesty |
| PR-2d.1 (optional) | Greedy score term for marginal target shortfall reduction |

---

## 10. Forbidden shortcuts

- `throughput_budget_satisfied := validation_passed` or `pipeline_ok`
- `placement_capacity_satisfied` as user-facing pass when `actual < target`
- Lowering `throughput_target_percent` only to greenwash without raising committed throughput
- Using reconstruction max as `placement_goal_count` without route-feasible caps
- Candidate order as commit proof; replay-as-input

---

## 11. Validation (narrow)

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_goal.py tests/unit/asteroid_lab/test_rttp_greedy_regret.py tests/unit/asteroid_lab/test_throughput_shortfall.py tests/unit/asteroid_lab/test_rttp_solver_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/placement_goal.py django_apps/asteroid_lab/optimization/selection/greedy_regret.py django_apps/asteroid_lab/optimization/pipeline.py
```

Ops smoke: record `solver_run_id` + `throughput_goal` JSON + whether primary pass met for reference slug.

---

## 12. Risks

- **Optimistic anchor cap** may set `placement_goal_count` above pairwise-feasible packings → more commit conflicts → attribute `commit_conflict_cap`.
- **High target %** on large maps may hit `max_placement_goal_count` before budget — expected; reason must be visible.
- **Runtime cost** grows with `placement_goal_count` (selection + commit probes) — bounded by config max.

---

## Appendix — Slug arithmetic (2026-05-24 ops)

```text
mineable_cells = 32
skeleton.capacity_goals = ceil(floor(32*0.75/5)/12) = 1
reconstruction_max = 32 * 480 = 15360
target (10%) = 1536
committed (v0.1) = 120 → bundles_needed = 13
```

PR-2d sets `placement_goal_count = 13` when caps allow (default max 32 does not bind). Commit/validation then determine how many of 13 survive re-probe and whether `actual >= 1536`.
