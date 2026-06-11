# Plan: SHA-2 - RouteDomainSnapshotBuilder (Low: lint cleanup)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-2
- Priority: Low
- Labels: refactor, bug, solver, spec
- Status at planning time: Todo

## Problem

Touched L3 files may accumulate lint issues after refactor; optional cleanup keeps gates green without functional change.

## Scope

- Run ruff/black on touched files and fix any new lint findings.

## Non-goals

- Unrelated refactors or behavior changes.

## Implementation Plan

1. Run `ruff check .` and `black --check .` on touched L3 modules.
2. Apply minimal formatting/lint fixes in files modified by SHA-2 work only.

## Files / Areas Likely Affected

- Files modified during SHA-2 High/Mid implementation

## Tests / Validation

- `ruff check .`
- `black --check .`

## Acceptance Criteria

- [ ] Lint and format gates pass on touched files

## Risks

- None significant; cosmetic only.

## Human Review Required

- no
- reason: Lint cleanup only.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on Mid-priority refactor completing first.
