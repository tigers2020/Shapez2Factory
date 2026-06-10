---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Reuse layer-walking logic and update Pattern Lab template

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

`explain_pattern_family_mismatch` already walks multi-layer codes layer-by-layer, but Pattern Lab analysis and template only render single-layer blocks. Per-layer canonical code, structural signature, rotation variants, and symbol maps are not surfaced.

## Scope

Reuse `explain_pattern_family_mismatch` layer-walking patterns in analysis output and update `pattern_lab.html` to render per-layer blocks.

## Non-goals

- Changing recipe graph validation behavior.
- Altering `MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN` constant.

## Implementation Plan

1. Read `explain_pattern_family_mismatch` layer-splitting logic in `pattern_lab_service.py` (around line 226).
2. Extract or mirror per-layer canonicalization into `analyze_pattern_lab_shape` multi-layer branch.
3. Build per-layer result objects: canonical code, signature, rotation variants, symbol map, distinct part count.
4. Update `django_apps/web/templates/web/pattern_lab.html` to iterate per-layer blocks (label each layer index).
5. Preserve existing single-layer template layout for backward compatibility.
6. Add unit test asserting multi-layer analysis returns N layer blocks for N-layer input.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `django_apps/web/templates/web/pattern_lab.html`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: `python manage.py check`
- manual verification: Each layer block shows signature, rotation variants, and symbol map

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Template complexity may grow; consider a partial include per layer block if the template exceeds maintainability.
