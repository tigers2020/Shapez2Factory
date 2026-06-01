---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-31
related_docs:
  - docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md
  - docs/superpowers/specs/2026-05-31-layer-03-route-probe-reachability-audit.md
---

# Layer 03 transport profile orchestration

## Problem

Layer 3 mixed `shape_belt` and `fluid_pipe` candidates in one expansion loop with a
concatenated goal list. That matches runtime behavior but hides the contract: each
transport profile has its own goals, anchors, and route probes before shared commit.

## Goal

Within the single `run_layer_03_rim_greedy_placement` orchestrator:

1. Derive active profiles from L1 `present_resource_kinds` / complete map field counts.
2. For each `TransportKind` profile: build profile-local `route_goals`, scan matching rim
   anchors only, run immediate weighted route probe.
3. Merge normal + diagnostic pools (D1 sort preserved).
4. Phase C1/D commit unchanged (shared `CommitReprobeContext` with all goals).

## Non-goals

- Splitting Layer 3 into separate layer slugs.
- Changing beam selection or commit reprobe policy.
- Renaming `ExteriorConnectionPlan.transport_kind` (separate PR).

## Contract

### `Layer03TransportProfile`

- `transport_kind: TransportKind`
- `resource_kind: ResourceKind`
- `route_goals: tuple[RouteGoal, ...]` — built from L2 plan for that transport only

### `build_layer03_transport_profiles(complete_map, exterior_plan)`

- One profile per present resource (`shape` → `SHAPE_BELT`, `fluid` → `FLUID_PIPE`).
- Canonical order: shape before fluid.
- Empty `exterior_plan` → empty tuple (caller handles skip).

### `generate_candidates_for_profile(...)`

- Only rim anchors whose `field_kind` matches the profile resource.
- `weighted_route_probe` receives **profile** `route_goals` only.

### `generate_candidates(...)`

- Calls each active profile, merges pools and expansion metrics.
- Behavior-preserving vs pre-refactor merged goal list (regression tests).

## Acceptance

- `tests/unit/asteroid_lab/layers/test_layer_03_transport_profile_orchestration.py`
- Existing `test_candidate_gen.py` and golden L3 tests remain green.
