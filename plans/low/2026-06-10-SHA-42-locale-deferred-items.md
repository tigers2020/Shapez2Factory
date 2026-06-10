---
linear_issue: SHA-42
title: CI never verifies committed locale/ko .po/.mo match build_locale_ko.py output
priority: Low
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Locale deferred items (SHA-42 Low scope)

## Source Issue

- Linear: SHA-42
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-42 priority breakdown lists low-priority follow-ups that are explicitly out of scope for the Mid CI drift gate: KO translation completeness (SHA-43) and replacing the polib builder with GNU gettext.

## Scope

Document and track deferred low-priority items. No implementation in the SHA-42 Mid gate PR unless explicitly pulled forward.

## Non-goals

- Implementing SHA-43 translation completeness work
- Migrating from polib to GNU gettext
- Changing CI drift gate behavior

## Implementation Plan

1. Confirm SHA-43 owns KO translation completeness (`build_locale_ko.py --strict` coverage expansion).
2. Add cross-link from SHA-42 Mid plan Risks section to SHA-43 if not already present.
3. If GNU gettext migration is ever requested, open a separate spec — do not bundle with drift gate.

## Files / Areas Likely Affected

- TBD (deferred to SHA-43 and future i18n cards)

## Validation Plan

- lint: N/A for tracking-only card
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm SHA-43 plan exists before starting translation work

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low items may be fully covered by SHA-43; this plan exists only because SHA-42 spec lists a Low priority section.
- GNU gettext migration has no open issue — create one if pursued.
