---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Other frontend bundle drift gates (deferred)

## Source Issue

- Linear: SHA-44 (Low priority breakdown — out of SHA-44 scope)
- Status at planning time: In Progress
- Priority: Low

## Problem

SHA-44 Low breakdown lists sibling committed-artifact drift gaps not addressed by the `app.css` gate:

1. Graph-layout bundles — SHA-35
2. Recipe-graph-editor bundles — SHA-40
3. Locale catalogs — SHA-42
4. Partial pytest substring guards in `test_asteroid_lab_ui_strings.py` (lab class strings only)

## Scope

**None for SHA-44.** Track via separate Linear issues; do not implement in SHA-44 Mid work.

## Non-goals

- Do not combine SHA-35/40/42 gates into SHA-44 PR.
- Do not expand substring UI string tests to replace full CSS rebuild gate.

## Implementation Plan

1. Land SHA-44 Mid `app.css` drift gate.
2. Implement SHA-35, SHA-40 per their own plans.
3. SHA-42 locale gate per `plans/mid/2026-06-10-SHA-42-locale-catalog-freshness-gate.md`.
4. Revisit lab UI substring tests only if product wants broader CSS class contract coverage.

## Files / Areas Likely Affected

- SHA-35: graph-layout build outputs (TBD in SHA-35 plan)
- SHA-40: recipe-graph-editor bundles (TBD)
- SHA-42: `locale/ko/LC_MESSAGES/*`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional future)

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Matches the source issue spec (deferred items documented).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Multiple separate CI Node jobs may increase wall time — consider shared setup composite action later (out of SHA-44 scope).
