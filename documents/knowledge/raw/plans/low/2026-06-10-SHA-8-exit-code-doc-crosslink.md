---
linear_issue: SHA-8
title: Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)
priority: Low
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Cross-link SHA-8 test with exit-code canonical docs (Low)

## Source Issue

- Linear: SHA-8
- Status at planning time: Todo
- Priority: Low

## Problem

After SHA-7 spec alignment, STACK_UNAVAILABLE (20) test should reference canonical exit-code documentation.

## Scope

Add docstring or comment in `test_cli_exit_codes.py` linking to artifact design spec §6.

## Non-goals

- No runtime changes.

## Implementation Plan

1. After SHA-7 Mid plan merges, add link comment near STACK_UNAVAILABLE test.
2. Verify spec §6 documents exit 20.

## Files / Areas Likely Affected

- `tests/unit/shapez2_factory/test_cli_exit_codes.py`
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Link resolves

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Blocked on SHA-7 doc update.
