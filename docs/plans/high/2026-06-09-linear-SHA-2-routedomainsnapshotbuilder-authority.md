# Plan: SHA-2 - Implement RouteDomainSnapshotBuilder as sole route_domain authority

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-2
- Priority: High
- Labels: refactor, bug, solver, spec
- Status at planning time: Todo

## Problem

Layer 03 commit-time re-probe and candidate route probing assemble `WeightedTransportRouteDomain` inline instead of using the canonical `RouteDomainSnapshotBuilder`. This violates spec R7 and the Asteroid Lab invariant that `RouteDomainSnapshotBuilder` is the sole owner of route-domain snapshots.

## Scope

- Introduce canonical `RouteDomainSnapshotBuilder` as the single construction point for route domain snapshots.
- Eliminate ad hoc inline domain assembly that can drift between probe and commit paths.

## Non-goals

- Changing route probe algorithm semantics.
- Reject reason mapping (SHA-3).
- Transport kind preservation (SHA-1).

## Implementation Plan

1. Implement `RouteDomainSnapshotBuilder.build_snapshot(...)` in the shared asteroid lab layer package, accepting `complete_map`, exterior plan, and equipment blockers per spec R7.
2. Replace inline construction in `candidate_gen.py` (~506-511) with builder call.
3. Replace inline construction in `commit_reprobe.py` (~95-100) with the same builder API.
4. Verify Phase B probe and Phase D reprobe produce identical domains for the same blocker set.

## Files / Areas Likely Affected

- New module under `src/shapez2_factory/application/asteroid_lab/layers/` (e.g. `route_domain_snapshot_builder.py`)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_reprobe.py`
- `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md` (reference only)
- `.cursor/rules/asteroid-lab-invariants.mdc` (invariant reference)

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/ -k "corridor or route_domain or commit" -q`
- `python manage.py check`

## Acceptance Criteria

- [ ] `RouteDomainSnapshotBuilder` is sole route domain construction point
- [ ] Candidate probe and commit reprobe use same builder API
- [ ] Regression test passes for identical blocker sets
- [ ] Existing commit finalize and narrow corridor tests pass

## Risks

- Builder API shape must match both probe contexts; incorrect signature causes subtle domain drift.
- Large architecture touch within L3 layer boundary — keep builder in application layer without adapter imports.

## Human Review Required

- yes
- reason: Introduces new canonical authority type and refactors hot-path domain assembly; architecture boundary change within solver stack.

## Automation Notes

Generated from Linear Todo issue by planning automation.
