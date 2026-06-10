---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Reuse explain_pattern_family_mismatch and update pattern_lab.html

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

`analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu')` returns error `"Pattern Lab currently supports single-layer shape codes only."` (lines 76–82 in `pattern_lab_service.py`), while `explain_pattern_family_mismatch('CuCuCuCu:CuCuCuCu', family_signature='AAAA', allow_rotation=False)` returns `None` (valid) per `test_explain_pattern_family_mismatch_multi_layer_each_layer_must_match`.

## Scope

Reuse `explain_pattern_family_mismatch` layer-walking logic for per-layer analysis output in `analyze_pattern_lab_shape`. Update `pattern_lab.html` to render per-layer canonical code, structural signature, rotation variants, and symbol map blocks.

## Non-goals

- Restoring `PatternCatalogRepository` DB macro lookup.
- Wiring `validate_recipe_graph_context` into production recompute.
- Changing `pattern_signature` normalization rules.

## Implementation Plan

1. In `pattern_lab_service.py`, replace single-layer-only gate (lines 76–82) with layer split up to `MAX_PATTERN_FAMILY_LAYERS` (4).
2. For each layer, call existing helpers used by `explain_pattern_family_mismatch` to build per-layer result DTO (canonical code, signature, rotations, symbol map).
3. Extend `analyze_pattern_lab_shape` return shape to carry `layers: list[...]` (or equivalent) for template consumption.
4. Update `pattern_lab.html` to iterate layers and render blocks (heading per layer index, same fields as single-layer view).
5. Ensure `public_pages.pattern_lab` passes multi-layer context unchanged.
6. Run `pytest tests/unit/shapez_solver/test_pattern_lab_service.py::test_explain_pattern_family_mismatch_multi_layer_each_layer_must_match -v` plus Pattern Lab service tests.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py` (`analyze_pattern_lab_shape`, `explain_pattern_family_mismatch`, `MAX_PATTERN_FAMILY_LAYERS`)
- `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py` (layer limit reference)
- `django_apps/web/templates/` — `pattern_lab.html`
- `django_apps/web/views/public_pages.py` (`pattern_lab`)
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: `python manage.py check`
- manual verification: Pattern Lab renders two layer blocks for `CuCuCuCu:CuCuCuCu`.

## Acceptance Criteria

- [ ] `analyze_pattern_lab_shape` uses layer-walking consistent with `explain_pattern_family_mismatch`.
- [ ] `pattern_lab.html` renders per-layer blocks.
- [ ] Single-layer codes produce identical output to pre-change behavior.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Return type change for `analyze_pattern_lab_shape` may require template and view adjustments together.
- Layer count > 4 should fail with clear error aligned to `MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN`.
