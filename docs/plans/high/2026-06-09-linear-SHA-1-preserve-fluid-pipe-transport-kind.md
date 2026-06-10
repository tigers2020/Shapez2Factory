# Plan: SHA-1 - Preserve fluid_pipe transport_kind in committed provisional overlay

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-1
- Priority: High
- Labels: bug, solver, spec
- Status at planning time: Todo

## Problem

Layer 03 commit finalization drops per-candidate `transport_kind` metadata. Every `ProvisionalPlacedCell` in the committed provisional overlay is stamped as `TransportKind.SHAPE_BELT`, mis-tagging fluid rim miners on mixed maps before L5 inner fill and replay consumers.

## Scope

- Fix correctness of transport tagging at commit time so downstream L5 and replay receive accurate `transport_kind` per placement.
- Ensure committed overlay reflects originating `BundleCandidate.transport_kind` for both shape belt and fluid pipe profiles.

## Non-goals

- Changing candidate generation logic (already correct).
- L5 inner fill implementation.
- Route domain builder work (SHA-2).

## Implementation Plan

1. Extend `CommittedRimSeedPlacement` in `src/shapez2_factory/application/asteroid_lab/layers/contracts/rim_greedy.py` with `transport_kind: TransportKind`.
2. Populate `transport_kind` in `_committed_placement` (commit finalize path) from `probed.candidate.transport_kind`.
3. Replace hardcoded `TransportKind.SHAPE_BELT` in `commit_finalize.py::_add_cells` (line ~220) with `placement.transport_kind`.
4. Update replay segment `layer03_rim_greedy_segment.py::_transport_wire()` to read per-placement transport instead of returning `SHAPE_BELT` for all placements.
5. Run targeted unit tests to confirm mixed-map fluid commits emit `FLUID_PIPE` in overlay and replay wire output.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/contracts/rim_greedy.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_finalize.py`
- `django_apps/asteroid_lab/layers/contracts/rim_greedy.py` (mirror if required by project convention)
- Replay segment under `django_apps/asteroid_lab/` or `src/shapez2_factory/adapters/asteroid_lab/replay/`
- `tests/unit/asteroid_lab/` transport orchestration and commit finalize tests

## Tests / Validation

- `pytest tests/unit/asteroid_lab/ -k "transport or commit_finalize" -q`
- `python manage.py check`
- `ruff check .`
- `mypy django_apps config src`

## Acceptance Criteria

- [ ] Committed placements retain candidate `transport_kind`
- [ ] Overlay cells match placement profile
- [ ] Mixed-map fluid commits show `FLUID_PIPE` in overlay and replay
- [ ] Unit tests pass for transport orchestration and commit finalize

## Risks

- DTO field addition may require updating all `CommittedRimSeedPlacement` constructors in tests and replay fixtures.
- Django mirror contract files must stay in sync with application layer DTO.

## Human Review Required

- no
- reason: Contract-aligned bugfix within existing L3 transport orchestration spec; no schema migration or auth change.

## Automation Notes

Generated from Linear Todo issue by planning automation.
