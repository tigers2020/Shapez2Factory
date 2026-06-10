# Plan: SHA-3 - Reprobe reject reason mapping (Low: documentation)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-3
- Priority: Low
- Labels: test, bug, solver
- Status at planning time: Todo

## Problem

Reject-reason mapping behavior should be documented in invariants manual for future regression authors.

## Scope

- Document commit-time reprobe → `RimGreedyRejectReason` mapping in asteroid lab invariants or testing manual.

## Non-goals

- Code behavior changes.

## Implementation Plan

1. Add short section to `documents/ai/manuals/testing.md` or asteroid lab invariants doc describing expected reject reason per probe failure mode.
2. Cross-reference SHA-3 fix and S1 narrow-corridor regression.

## Files / Areas Likely Affected

- `documents/ai/manuals/testing.md` or `.cursor/rules/asteroid-lab-invariants.mdc` reference doc

## Tests / Validation

- Docs-only; no runtime gate required beyond review.

## Acceptance Criteria

- [ ] Mapping documented for commit-time reprobe failures

## Risks

- None.

## Human Review Required

- no
- reason: Documentation only.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on Mid-priority implementation completing first.
