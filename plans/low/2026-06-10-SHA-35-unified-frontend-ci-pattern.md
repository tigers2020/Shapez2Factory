---
linear_issue: SHA-35
title: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI pattern

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Low

## Problem

Graph-layout, CSS, locale, and recipe-graph-editor bundles each need freshness gates. A unified CI pattern would reduce duplication.

## Scope

- Document or prototype unified static-asset rebuild+diff CI pattern after Mid graph-layout gate lands.

## Non-goals

- Implementing SHA-40, SHA-44, SHA-42 gates in this card.

## Implementation Plan

1. After SHA-35 Mid gate merges, survey SHA-40/44/42 patterns.
2. Propose shared CI script for `build:*` + `git diff` checks.
3. Track unified pattern as follow-up if worthwhile.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/` (TBD shared freshness script)

## Validation Plan

- manual verification: CI pattern review

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Deferred; depends on Mid plan.
