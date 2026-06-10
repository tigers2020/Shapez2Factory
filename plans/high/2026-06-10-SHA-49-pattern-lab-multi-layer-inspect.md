---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: High
labels:
  - bug
  - ui
  - test
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Enable Pattern Lab inspection for valid multi-layer recipe targets

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: High

## Problem

Pattern Lab (`analyze_pattern_lab_shape`) hard-rejects any multi-layer shape code (`:`-separated), but the same codebase already supports per-layer pattern-family checks for up to four layers via `explain_pattern_family_mismatch` (used by `validate_recipe_graph_context` and recipe graph shape limits). Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that are valid in recipe graphs.

## Scope

Extend Pattern Lab analysis and UI so staff can inspect multi-layer codes up to the existing four-layer contract (`MAX_PATTERN_FAMILY_LAYERS = 4`), consistent with recipe graph behavior. Single-layer behavior must not regress.

## Non-goals

- Restoring removed `PatternCatalogRepository` DB macro lookup (tables dropped in migration `0009_drop_pattern_catalog_tables`).
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family).
- Changing `pattern_signature` normalization rules.

## Implementation Plan

1. Repro: `python3 -c "from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape; print(analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu').error)"` → hard rejection today.
2. Remove or replace hard reject at `pattern_lab_service.py` lines 76–82 for codes with up to four `:`-separated layers.
3. Reuse `explain_pattern_family_mismatch` layer-walking for per-layer canonical code, structural signature, rotation variants, and symbol map output.
4. Update `django_apps/web/templates/.../pattern_lab.html` (via `public_pages.pattern_lab`) to render per-layer blocks.
5. Manual verify: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows per-layer analysis, not error string.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py` (`analyze_pattern_lab_shape`, `explain_pattern_family_mismatch`, `MAX_PATTERN_FAMILY_LAYERS`)
- `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py` (`MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN = 4` — reference)
- `django_apps/web/views/public_pages.py` (`pattern_lab` view)
- `django_apps/web/templates/` — `pattern_lab.html`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`
- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py tests/integration/web/test_pattern_lab.py -v`
- build: `python manage.py check`
- manual verification: Staff Pattern Lab page with `CuCuCuCu:CuCuCuCu` shows per-layer signature/rotation/symbol output.

## Acceptance Criteria

- [ ] Multi-layer codes up to four layers analyze without hard rejection.
- [ ] Per-layer signature/rotation/symbol output rendered in UI.
- [ ] Single-layer behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- UI layout for four layers may need template structure beyond current single-layer blocks.
- `explain_pattern_family_mismatch` returns `None` for valid multi-layer codes — Pattern Lab must surface success output, not only mismatch errors.
