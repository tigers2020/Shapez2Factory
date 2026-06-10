# Plan: SHA-3 - Reprobe reject reason mapping (Mid: structured return and tests)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-3
- Priority: Mid
- Labels: test, bug, solver
- Status at planning time: Todo

## Problem

Boolean-only reprobe return and loose regression assertions prevent locking correct reject-reason behavior.

## Scope

- Define structured reprobe result type.
- Implement enum mapping logic.
- Tighten S1 narrow-corridor regression to single expected reason.

## Non-goals

- Probe algorithm changes.
- SHA-2 builder work.

## Implementation Plan

1. Introduce structured return type (e.g. `CommitReprobeResult` with success flag + optional `RimGreedyRejectReason` + probe diagnostics).
2. Update `finalize_selection` mapping table from probe status → enum (cover unreachable, hard blocker, and other defined reasons).
3. Update `test_narrow_corridor_regression.py` (~86-89) to assert one expected reason instead of 3-way union.
4. Add unit test for unreachable vs hard-blocker distinction at commit finalize.

## Files / Areas Likely Affected

- `commit_reprobe.py`, `commit_finalize.py`
- `tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py`
- New or extended commit finalize unit tests

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py::test_* -q`

## Acceptance Criteria

- [ ] Structured reprobe return type in place
- [ ] Enum mapping logic complete
- [ ] S1 regression tightened to single reason

## Risks

- Mapping table must align with all probe failure modes or tests will flake.

## Human Review Required

- no
- reason: Implementation detail of High-priority diagnostic fix.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on High-priority mapping fix scope in `docs/plans/high/2026-06-09-linear-SHA-3-reprobe-reject-reason-mapping.md`.
