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

# Plan: Pattern Lab UI per-layer rendering

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

Even after service-layer multi-layer support (High plan), `pattern_lab.html` and `public_pages.pattern_lab` only render a single analysis block. Staff need per-layer signature, rotation variants, and symbol map sections consistent with recipe graph four-layer contract.

## Scope

Update view context and template to render per-layer analysis blocks for multi-layer codes. Reuse display patterns from existing single-layer sections.

## Non-goals

- Recipe graph editor changes.
- Pattern catalog DB restoration.

## Implementation Plan

1. Read `django_apps/web/views/public_pages.py` `pattern_lab` view and `django_apps/web/templates/web/pattern_lab.html`.
2. Pass multi-layer analysis structure from updated `analyze_pattern_lab_shape` return value.
3. Template: loop layers with headings (`Layer 0`, `Layer 1`, …); render signature, symbol map table, rotation variants per layer.
4. Single-layer codes: keep current layout (no visual regression).
5. Reuse `explain_pattern_family_mismatch` layer-walking semantics for consistency with recipe validation messaging where applicable.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `django_apps/web/templates/web/pattern_lab.html`
- `django_apps/shapez_solver/services/pattern_lab_service.py` (context shape from High plan)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: existing `tests/integration/web/test_pattern_lab.py` must still pass for single-layer
- build: N/A
- manual verification: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows two layer sections

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Template gettext strings for new layer headings may need `build_locale_ko.py` regen if trans tags added (separate from SHA-42 gate timing).
