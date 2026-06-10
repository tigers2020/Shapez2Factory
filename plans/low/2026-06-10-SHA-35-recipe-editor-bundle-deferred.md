---
linear_issue: SHA-35
title: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source
priority: Low
labels:
  - automation
  - infra
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred unified frontend static-asset CI (SHA-35 low scope)

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Low

## Problem

Recipe graph editor bundle drift and a unified frontend static-asset CI pattern are tracked separately (SHA-40) and deferred from SHA-35 mid scope.

## Scope

- Note SHA-40 linkage in PR description after mid CI gate lands.
- Optional: add a one-line cross-reference in `validation-routine.md`.

## Non-goals

- Implementing recipe graph editor CI in SHA-35.

## Implementation Plan

1. After graph-layout freshness gate merges, verify SHA-40 remains the owner for recipe editor bundles.
2. Add cross-reference in docs if contributors confuse the two bundle paths.

## Files / Areas Likely Affected

- `docs/agent-workflows/validation-routine.md` (optional)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: SHA-40 still open in Linear

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- None — documentation-only deferral.
