---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Pattern Lab per-layer UI rendering

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

After High-scope service support lands, `pattern_lab.html` must render per-layer signature, rotation variants, and symbol map blocks for multi-layer codes.

## Scope

Update Pattern Lab template and view wiring to display per-layer analysis output from `analyze_pattern_lab_shape`.

## Non-goals

- Pattern catalog DB restoration
- Recipe graph production recompute wiring

## Implementation Plan

1. Extend `pattern_lab.html` with per-layer block layout (reuse single-layer partials where possible).
2. Wire `public_pages.pattern_lab` view to pass multi-layer result structure to template.
3. Verify staff page GET with multi-layer query param renders all layers.

## Files / Areas Likely Affected

- `django_apps/web/templates/web/pattern_lab.html` (or equivalent path)
- `django_apps/web/views/public_pages.py`
- `django_apps/shapez_solver/services/pattern_lab_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: N/A
- manual verification: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows per-layer blocks

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan service changes completing first.
