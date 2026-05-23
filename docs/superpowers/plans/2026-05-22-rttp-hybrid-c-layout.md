# RTTP Hybrid C Layout — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reintroduce post-reconstruction optimization as **Hybrid C** (skeleton → linear bundle candidates → regret selection → commit/LNS) per [`2026-05-22-rttp-hybrid-c-layout-design.md`](../specs/2026-05-22-rttp-hybrid-c-layout-design.md).

**Architecture:** Four packages under `django_apps/asteroid_lab/optimization/` (recreated after strip-solver). `reconstruction/` stays free of `optimization` imports. Wire `solver_runtime_entry` only after PR-5 gate tests pass.

**Tech Stack:** Python 3.12+, Django 5.2, frozen dataclasses, `StrEnum`, pytest; CANON throughput [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md).

**Baseline policy:** [`2026-05-22-rttp-worktree-baseline.md`](../reports/2026-05-22-rttp-worktree-baseline.md) — full fast suite green (1044+); RTTP `test_rttp_*` must green; do not increase failure count.

**Out of v0.1:** MacroBundle T3, merger auto-place, full 2F JPS, CP-SAT, validation route repair.

**Worktree:** `F:\Python_Projects\shapez2Factory\.worktrees\rttp-hybrid-c` · branch `feature/rttp-hybrid-c`  
**Plan status:** Ready for execution (self-review 2026-05-22)

---

## Spec → plan coverage

| Spec section | Plan slice |
|--------------|------------|
| Layer 1 `RttpSkeleton` | PR-1 (+ minimal `OptimizationInput` stub) |
| Layer / lane abstraction | PR-2 `lift_lane_domain.py` |
| Layer 2 candidates + probe | PR-3 |
| Layer 3 greedy-regret | PR-4 |
| Layer 4 commit + LNS + validation read-only | PR-5 |
| RTTP-G1–G8 | PR-1..5 tests (see gate column per PR) |
| Map class P0 greenfield | PR-1 conftest + PR-5 pipeline test |
| Map class P1 existing trunk | PR-6 (after PR-5) |
| v1 MacroBundle T3 | §v1 follow-on only |
| Non-goals (merger, JPS, CP-SAT) | Out of v0.1 header |

---

## Package layout (target)

```text
django_apps/asteroid_lab/optimization/
  __init__.py
  coords.py                    # re-export Coord from snapshots.grid_contract only
  input_contracts.py           # OptimizationInput, RouteGoal, TransportKind, ...
  reconstruction_adapter.py      # optimization_input_from_reconstruction (no shadow/RD)
  skeleton/
    __init__.py
    rttp_skeleton.py            # RttpSkeleton DTO
    ring_builder.py             # full / C-spine / one-side spine
    skeleton_builder.py         # RttpSkeletonBuilder.build(...)
  routing/
    __init__.py
    lift_lane_domain.py         # LiftEdge, trunk mask, layer/lane v0.1
    route_probe.py              # bounded BFS stub→lift→trunk→goal
    route_domain.py             # RouteCellDomain builder (skeleton-aware)
  candidates/
    __init__.py
    pattern_library.py          # linear extractor+0..3 ext (Phase 2 parity)
    candidate_dtos.py           # BundleCandidate, ExtractorPlacementPolicy, enums
    candidate_generator.py      # generate + probe integration
  selection/
    __init__.py
    equivalence.py              # CandidateEquivalenceKey dedupe
    greedy_regret.py            # regret + inlet_fragility + fragmentation
  commit/
    __init__.py
    incremental_commit.py       # re-probe, inlet rule, reservations
    local_lns.py                # bounded repair loop
  validation/
    __init__.py
    final_validation.py         # read-only asserts only
  pipeline.py                   # orchestrate layers 1–4 for tests/runtime
```

---

## Pre-flight (before PR-1)

- [ ] **Step 1:** Confirm strip gates on branch tip

```powershell
rg "from django_apps\.asteroid_lab\.optimization|import django_apps\.asteroid_lab\.optimization" django_apps/asteroid_lab/reconstruction
# Expected: no matches

Test-Path django_apps/asteroid_lab/optimization
# Expected: False
```

- [ ] **Step 2:** Read spec gates RTTP-G1~G8 and baseline report.

- [ ] **Step 3:** Create package skeleton (empty `__init__.py` only) — commit `chore(optimization): scaffold RTTP package layout`

---

## PR-1 — Skeleton (Layer 1) — RTTP-G1, RTTP-G2

**Gate:** deterministic `RttpSkeleton`; no equipment in output.

**Files:**

- Create: `optimization/__init__.py`, `optimization/coords.py` (re-export only)
- Create: `optimization/input_contracts.py` — **minimal** frozen `OptimizationInput` + `RttpSkeletonConfig` (mineable, rim, inner, external_void, protected, transport kind only; full `route_goals` / adapter in PR-2)
- Create: `optimization/skeleton/rttp_skeleton.py`, `ring_builder.py`, `skeleton_builder.py`
- Create: `tests/unit/asteroid_lab/conftest.py` — `greenfield_optimization_input` factory (≤20 mineable cells, no replay)
- Create: `tests/unit/asteroid_lab/test_rttp_skeleton.py`

- [ ] **Step 0:** Scaffold empty package dirs per layout — commit `chore(optimization): scaffold RTTP package layout` (if not done in pre-flight).

- [ ] **Step 1: Write failing test** `test_rttp_skeleton_deterministic_for_same_input`

```python
def test_rttp_skeleton_deterministic_for_same_input(greenfield_optimization_input):
    a = RttpSkeletonBuilder.build(greenfield_optimization_input, config=default_config())
    b = RttpSkeletonBuilder.build(greenfield_optimization_input, config=default_config())
    assert a == b
    assert a.skeleton_id == b.skeleton_id
```

- [ ] **Step 2:** Run `python -m pytest tests/unit/asteroid_lab/test_rttp_skeleton.py::test_rttp_skeleton_deterministic_for_same_input -v` — expect FAIL.

- [ ] **Step 3:** Implement `RttpSkeleton` frozen dataclass (fields per spec §Layer 1). Implement ring option enumeration + `skeleton_score` pick. Set `capacity_goals` from CANON ratios (shape: `ceil(platforms/12)`, fluid: `ceil(platforms/72)` heuristic from mineable footprint / 5 cells — document constants in `skeleton_builder.py`).

- [ ] **Step 4:** Add `test_rttp_skeleton_has_no_equipment_cells` — skeleton only sets coord sets / ports / lift_columns, never miner types.

- [ ] **Step 5:** Run `python -m pytest tests/unit/asteroid_lab/test_rttp_skeleton.py -v` — PASS.

- [ ] **Step 6:** `python -m ruff check django_apps/asteroid_lab/optimization/skeleton tests/unit/asteroid_lab/test_rttp_skeleton.py`

- [ ] **Step 7:** Commit `feat(rttp): add deterministic RTTP skeleton builder (G1,G2)`

**Greenfield fixture:** add `tests/unit/asteroid_lab/conftest.py` helper building minimal `OptimizationInput` from `acceptance_topology_from_reconstruction` on a tiny synthetic reconstruction or frozen mineable grid (≤ 20 cells). No replay JSON as input.

---

## PR-2 — Adapter + lift/lane domain (Layer 1→2 bridge) — RTTP-G5 prep

**Gate:** `optimization_input_from_reconstruction`; lift edge in route domain.

**Files:**

- Create: `optimization/input_contracts.py`, `reconstruction_adapter.py`
- Create: `optimization/routing/lift_lane_domain.py`, `route_domain.py`
- Create: `tests/unit/asteroid_lab/test_rttp_lift_lane_domain.py`
- Create: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`

- [ ] **Step 1:** Test `test_optimization_input_adapter_server_coords_only` — all coords ints, no raw x in DTO.

- [ ] **Step 2:** Test `test_lift_edge_connects_stub_to_trunk_mask` — surrounded platform coord still has path via `LiftEdge` in domain (RTTP-G5).

- [ ] **Step 3:** Implement adapter using `acceptance_topology.py` + `topology_contract` / rim extraction (reuse patterns from deleted adapter only as reference in git history — reimplement minimal).

- [ ] **Step 4:** Implement `LiftEdge(platform_coord, lift_coord, lane_id)` and `RouteCellDomain` with trunk mask from skeleton.

- [ ] **Step 5:** pytest both files green; ruff; commit `feat(rttp): optimization input adapter and lift/lane route domain`

---

## PR-3 — Pattern library + candidates + probe (Layer 2) — RTTP-G3

**Gate:** `INTERIOR_AND_RIM` reachable-only normal pool; probe before pool.

**Files:**

- Create: `optimization/candidates/pattern_library.py`, `candidate_dtos.py`, `candidate_generator.py`
- Create: `optimization/routing/route_probe.py`
- Create: `tests/unit/asteroid_lab/test_rttp_candidate_generator.py`

- [ ] **Step 1:** Test `test_candidate_generator_does_not_commit` (parity with old `test_candidate_generator_does_not_commit_placements`).

- [ ] **Step 2:** Test `test_interior_and_rim_unreachable_goes_to_rejected` — block goal → not in normal pool.

- [ ] **Step 3:** Test `test_reachable_candidate_in_normal_pool` — greenfield + skeleton + one valid anchor.

- [ ] **Step 4:** Implement linear patterns: extension_count 0..3, canonical E rotation, `throughput_factor` 4/8/12/16.

- [ ] **Step 5:** Implement generator: anchor ∈ `rim ∪ inner_cells`; immediate `RouteProbe` with budget; `CandidateRejectReason` StrEnum.

- [ ] **Step 6:** pytest + ruff; commit `feat(rttp): bundle candidates with skeleton-aware route probe (G3)`

---

## PR-4 — Greedy-regret selection (Layer 3) — RTTP-G4

**Gate:** `commit_order` explicit; order ≠ rim scan order.

**Files:**

- Create: `optimization/selection/equivalence.py`, `greedy_regret.py`
- Create: `tests/unit/asteroid_lab/test_rttp_greedy_regret.py`

- [ ] **Step 1:** Test `test_regret_prefers_high_scarcity_candidate` — controlled two-candidate fixture.

- [ ] **Step 2:** Test `test_commit_order_is_explicit_not_rim_scan` — genome list ids ≠ sorted rim cell order.

- [ ] **Step 3:** Implement dedupe key: `occupied_cells`, `output_stub`, `output_dir`, `transport_kind`, `base_throughput`, `topology_signature`.

- [ ] **Step 4:** Implement `priority = base_score + λ*regret - inlet_fragility - fragmentation` (constants in config dataclass, not magic strings).

- [ ] **Step 5:** pytest + ruff; commit `feat(rttp): greedy-regret selection with explicit commit_order (G4)`

---

## PR-5 — Commit, inlet, LNS, pipeline (Layer 4) — RTTP-G6, RTTP-G7, RTTP-G8

**Gate:** inlet enum reject; LNS only post-failure; greenfield golden.

**Files:**

- Create: `optimization/commit/incremental_commit.py`, `local_lns.py`
- Create: `optimization/validation/final_validation.py`, `pipeline.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py` (wire pipeline behind config flag, default off until tests green)
- Create: `tests/unit/asteroid_lab/test_rttp_commit.py`, `test_rttp_lns.py`, `test_rttp_pipeline_greenfield.py`

- [ ] **Step 1:** Test `test_commit_rejects_inlet_on_shared_transport` — `CommitConflictReason.INLET_ON_SHARED_TRANSPORT`.

- [ ] **Step 2:** Test `test_commit_reprobes_latest_domain` — domain version increments between candidates.

- [ ] **Step 3:** Test `test_lns_only_runs_after_commit_failure` — validation module has no repair imports.

- [ ] **Step 4:** Test `test_greenfield_pipeline_commits_n_bundles` (RTTP-G8) — deterministic N, replay on/off same candidate ids (skeleton replay artifact optional).

- [ ] **Step 5:** Implement incremental commit + reservation merge into trunk mask.

- [ ] **Step 6:** Implement bounded LNS (radius R, max iterations, time budget).

- [ ] **Step 7:** Implement `run_rttp_pipeline(optimization_input, config) -> PipelineResult` used by tests first.

- [ ] **Step 8:** Optional: enable `solver_runtime_entry` when `config["rttp_enabled"]=True` and all gates pass — separate commit.

- [ ] **Step 9:** Run targeted suite:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_skeleton.py `
  tests/unit/asteroid_lab/test_rttp_lift_lane_domain.py `
  tests/unit/asteroid_lab/test_optimization_input_adapter.py `
  tests/unit/asteroid_lab/test_rttp_candidate_generator.py `
  tests/unit/asteroid_lab/test_rttp_greedy_regret.py `
  tests/unit/asteroid_lab/test_rttp_commit.py `
  tests/unit/asteroid_lab/test_rttp_lns.py `
  tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py -v
```

- [ ] **Step 10:** Compare fast suite counts vs baseline report (must not increase failures/errors).

- [ ] **Step 11:** Update `documents/Algorithm/asteroid_lab_10_development_sequence.md` checkboxes for Sequences 2–7 as each PR merges.

---

## Enum / contract requirements (all PRs)

Use `StrEnum` (no free-form `failure_reason` / `issue_code`):

```python
class CandidateRejectReason(StrEnum): ...
class CommitConflictReason(StrEnum):
    INLET_ON_SHARED_TRANSPORT = "inlet_on_shared_transport"
    ...
```

Import `Coord` only via `optimization/coords.py` → `snapshots.grid_contract`.

---

## Merge checklist

| Item | Command / evidence |
|------|-------------------|
| RTTP-G1~G8 | targeted pytest green (PR-5 step 9) |
| reconstruction import boundary | `rg` pre-flight zero matches |
| Fast suite regression | failures ≤ 6, errors ≤ 10 vs baseline |
| ruff | `python -m ruff check django_apps/asteroid_lab/optimization` |
| mypy (PR gate) | `python -m mypy django_apps/asteroid_lab/optimization` when package stable |

---

## PR-6 — Existing trunk (P1 map class) — post PR-5

**Gate:** skeleton seeds `trunk_mask_cells` from `existing_trunk_cells`; at least one candidate reaches trunk attachment goal.

**Files:**

- Modify: `optimization/skeleton/skeleton_builder.py` — merge `existing_trunk_cells` into trunk mask
- Modify: `optimization/reconstruction_adapter.py` — populate trunk from reconstruction
- Create: `tests/unit/asteroid_lab/test_rttp_existing_trunk.py`

- [ ] **Step 1:** Test `test_skeleton_includes_existing_trunk_cells` on fixture with non-empty trunk (use reconstruction fixture line or minimal synthetic).

- [ ] **Step 2:** Test `test_reachable_candidate_attaches_to_existing_trunk` — one commit path in probe-only or pipeline dry-run.

- [ ] **Step 3:** pytest + ruff; commit `test(rttp): existing trunk map class P1`

Run only after PR-5 targeted suite is green.

---

## v1 follow-on (separate spec/plan)

- `MacroBundleT3` compiler
- Dense interior regret on macro slots
- Merger on trunk, JPS profiling

Do not start v1 until v0.1 PR-5 merges and targeted gates stay green.

---

## Execution handoff

Plan saved: `docs/superpowers/plans/2026-05-22-rttp-hybrid-c-layout.md` (commit `b03950a7` on `feature/rttp-hybrid-c`; amend or follow-up commit if this self-review section is edited).

**Choose execution mode:**

1. **Subagent-driven (recommended)** — fresh subagent per PR (1→6), review between PRs; skill: `subagent-driven-development`
2. **Inline** — this session runs pre-flight + PR-1 with checkpoints; skill: `executing-plans`

Reply with `1` or `2` (or `PR-1 inline` to start pre-flight + skeleton only).
