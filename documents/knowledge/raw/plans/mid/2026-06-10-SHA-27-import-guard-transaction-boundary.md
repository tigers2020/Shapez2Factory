---
linear_issue: SHA-27
title: game_data import commits before post-import guards run (fail-open on invariant violation)
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Move post-import guards inside transaction boundary

## Source Issue

- Linear: SHA-27
- Status at planning time: Todo
- Priority: Mid

## Problem

`GameDataImporter.run()` runs `run_post_import_guards()` after `transaction.atomic()` exits. Guard failure leaves committed invalid import batch.

## Scope

Run guards before commit (inside atomic block) so `AssertionError` rolls back transaction.

## Implementation Plan

1. Read `django_apps/game_data/importers/importer.py` transaction structure.
2. Move `run_post_import_guards()` to end of `transaction.atomic()` block.
3. Add integration test injecting guard failure → assert rollback/no partial data.
4. Run game_data importer tests.

## Files / Areas Likely Affected

- `django_apps/game_data/importers/importer.py`
- `django_apps/game_data/services/import_guards.py`
- tests under `tests/unit/game_data/` or integration (TBD)

## Validation Plan

- tests: importer + guard failure injection test
- lint: `ruff check django_apps/game_data/`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-13 export boundary is separate.
- Low: document unwired guards.
