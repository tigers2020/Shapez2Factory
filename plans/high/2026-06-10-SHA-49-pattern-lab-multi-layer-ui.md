---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Enable Pattern Lab multi-layer shape inspection

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: High

## Problem

Pattern Lab (`analyze_pattern_lab_shape`) hard-rejects any multi-layer shape code (`:`-separated), but the same codebase already supports per-layer pattern-family checks for up to four layers via `explain_pattern_family_mismatch`. Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that are valid in recipe graphs.

## Scope

Remove the single-layer hard rejection in Pattern Lab analysis so staff can inspect valid multi-layer recipe targets (up to four layers) in the UI.

## Non-goals

- Restoring removed `PatternCatalogRepository` DB macro lookup.
- Wiring `validate_recipe_graph_context` into production recompute.
- Changing `pattern_signature` normalization rules.

## Implementation Plan

1. Read `analyze_pattern_lab_shape` in `django_apps/shapez_solver/services/pattern_lab_service.py` (lines 76–82 single-layer gate).
2. Replace the hard `_error_result` for multi-layer codes with per-layer analysis using existing helpers (`pattern_signature`, `_build_symbol_map`, `_build_rotation_variants`).
3. Split colon-separated input into layers (respect `MAX_PATTERN_FAMILY_LAYERS = 4`); return structured per-layer results instead of error.
4. Extend `PatternLabAnalysis` or add a companion DTO for multi-layer output if the current dataclass cannot hold per-layer blocks.
5. Wire the view `public_pages.pattern_lab` to pass multi-layer results to the template.
6. Manually verify `GET /solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` renders per-layer output (not an error page).

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `django_apps/web/views/public_pages.py`
- `django_apps/web/templates/web/pattern_lab.html`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: `python manage.py check`
- manual verification: Pattern Lab page with `CuCuCuCu:CuCuCuCu` shows per-layer analysis

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `PatternCatalogRepository` macro lookup may remain single-pattern only; multi-layer DB candidate display may need per-layer or omitted candidates.
