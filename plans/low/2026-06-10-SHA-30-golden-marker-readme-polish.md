---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Low
labels:
  - test
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Golden harness marker and README polish (SHA-30 Low)

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority wiring, optional polish can improve contributor discoverability: pytest marker organization and README examples for adding golden pairs.

## Scope

Optional: pytest marker organization and README polish for golden harness workflow.

## Non-goals

- No new golden fixtures beyond Mid plan scope.
- No CI topology changes unless trivial doc cross-link.

## Implementation Plan

1. After Mid plan lands, review pytest marker naming (`golden`, `integration`) for consistency with existing markers.
2. Add short "Adding a golden test" section to `tests/golden/README.md` with copy-paste template.
3. Cross-link from `documents/ai/manuals/testing.md` if golden harness is part of canonical test tiers.
4. Verify marker filter docs in `structure.md` or agent workflows if golden tier is documented there.

## Files / Areas Likely Affected

- `tests/golden/README.md`
- `documents/ai/manuals/testing.md` (optional cross-link)
- `structure.md` (optional tier note)
- TBD — pytest config if marker rename needed

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: README instructions reproducible by following steps

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion.
- Manual testing doc updates may need governance line-count check (non-blocking WARN ok).
