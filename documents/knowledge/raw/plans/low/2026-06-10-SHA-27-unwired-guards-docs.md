---
linear_issue: SHA-27
title: game_data import commits before post-import guards run (fail-open on invariant violation)
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document unwired import guards (SHA-27 Low)

## Source Issue

- Linear: SHA-27
- Priority: Low

## Scope

Document guards like `assert_canonical_ids_unique` if not wired in `run_post_import_guards`.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional inventory in import_guards.py module docstring.
