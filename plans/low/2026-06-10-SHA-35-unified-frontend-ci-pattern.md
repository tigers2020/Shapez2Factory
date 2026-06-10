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

# Plan: Unified frontend static-asset CI pattern (SHA-35 Low)

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Low

## Problem

Recipe graph editor bundle drift (SHA-40) and other frontend static assets may benefit from a unified CI freshness pattern after graph-layout gate lands.

## Scope

Optional: document unified frontend static-asset CI pattern linking SHA-35 and SHA-40.

## Non-goals

- Implementing SHA-40 in this slice.

## Implementation Plan

1. After Mid CI gate lands, add note in `frontend.md` referencing pattern for future bundles.
2. Cross-link SHA-40 for recipe graph editor follow-up.

## Files / Areas Likely Affected

- `documents/ai/manuals/frontend.md`

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Doc readable

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Deferred unified pattern until SHA-40 scoped.
