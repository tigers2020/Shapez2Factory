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

# Plan: Render per-layer Pattern Lab blocks from explain_pattern_family_mismatch

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

Even after service support, `pattern_lab.html` only renders single-layer analysis blocks. Multi-layer output needs per-layer canonical code, structural signature, rotation variants, and symbol map sections.

## Scope

Update Pattern Lab template and view context to render per-layer analysis blocks for colon-separated codes.

## Non-goals

- Recipe graph editor changes.
- Pattern catalog DB restoration.

## Implementation Plan

1. Extend `analyze_pattern_lab_shape` return DTO to include per-layer result list (canonical code, signature, rotation variants, symbol map per layer).
2. Update `pattern_lab.html` to iterate layers and render blocks consistent with existing single-layer layout.
3. Ensure `MAX_PATTERN_FAMILY_LAYERS` and `MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN` stay aligned (both 4).
4. Add view-level error handling for codes exceeding four layers.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `django_apps/shapez_solver/templates/shapez_solver/pattern_lab.html`
- `django_apps/web/views/public_pages.py` (pattern lab view, if present)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: N/A
- manual verification: Multi-layer GET renders distinct per-layer sections

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Per-layer signature/rotation/symbol output rendered.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Template complexity may require small partial extraction; keep within existing Django template style.
