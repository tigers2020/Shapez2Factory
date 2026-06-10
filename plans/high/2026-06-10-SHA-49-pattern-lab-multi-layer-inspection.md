---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Enable Pattern Lab multi-layer shape inspection

## Source Issue

- Linear: SHA-49
- Status at planning time: In Progress
- Priority: High

## Problem

`analyze_pattern_lab_shape` hard-rejects any multi-layer shape code (`:`-separated) with `"Pattern Lab currently supports single-layer shape codes only."`, while `explain_pattern_family_mismatch` already walks up to four layers (`MAX_PATTERN_FAMILY_LAYERS = 4`). Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that are valid in recipe graphs.

## Scope

Remove the single-layer hard rejection in `analyze_pattern_lab_shape` and return per-layer analysis for colon-separated codes up to four layers. Preserve existing single-layer behavior and error paths (parse errors, empty input, >4 layers).

## Non-goals

- Restoring removed `PatternCatalogRepository` DB macro lookup (tables dropped in migration `0009_drop_pattern_catalog_tables`)
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family)
- Changing `pattern_signature` normalization rules

## Implementation Plan

1. Reproduce current failure: `python3 -c "from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape; print(analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu').error)"` — expect single-layer-only error.
2. Introduce a `PatternLabLayerAnalysis` dataclass (layer index, canonical code, signature, symbol_map, rotation_variants, distinct_part_count) and extend `PatternLabAnalysis` with `layers: tuple[PatternLabLayerAnalysis, ...]` (empty for error-only results; single-layer may keep top-level fields for backward compatibility).
3. Replace the `is_single_layer()` early return (lines 76–82 in `pattern_lab_service.py`) with layer iteration modeled on `explain_pattern_family_mismatch`: parse shape, reject when `len(target_shape.layers) > MAX_PATTERN_FAMILY_LAYERS`, build per-layer canonical code from quadrants.
4. For each layer, compute `pattern_signature`, `_build_symbol_map`, and `_build_rotation_variants` on the layer's 8-char code (reuse existing helpers; `_shape_tokens` already returns empty for `:` codes — pass layer-local code without colon).
5. Keep DB macro candidate lookup at whole-shape or per-layer signature — prefer per-layer signature lookup to match inspection intent; document choice in code if whole-shape lookup is retained for layer 0 only.
6. Add unit test `test_pattern_lab_analyzes_multi_layer_shape` in `tests/unit/shapez_solver/test_pattern_lab_service.py` asserting no error, two layers, distinct per-layer signatures for `CuCuCuCu:CuCuCuCu`.
7. Add unit test `test_pattern_lab_rejects_more_than_four_layers` aligned with `MAX_PATTERN_FAMILY_LAYERS`.
8. Confirm single-layer tests (`test_pattern_lab_analyzes_signature_without_db_candidates`, `test_pattern_lab_reports_parse_error`) still pass unchanged.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: `python manage.py check`
- manual verification: Pattern Lab GET with `code=CuCuCuCu:CuCuCuCu` shows analysis (after UI plan lands)

## Acceptance Criteria

- [ ] Multi-layer codes up to four layers analyze without hard rejection.
- [ ] Per-layer signature data available from service layer.
- [ ] Single-layer behavior unchanged.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- `PatternLabAnalysis` shape change may require view/template updates (covered in Mid plan).
- DB macro candidate scope for multi-layer: per-layer vs first-layer only — default to per-layer signature match.
