---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Pattern Lab multi-layer analysis support

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: High

## Problem

Pattern Lab (`analyze_pattern_lab_shape`) hard-rejects any multi-layer shape code (`:`-separated), but recipe graph validation already supports per-layer pattern-family checks up to four layers via `explain_pattern_family_mismatch`. Staff cannot inspect signatures, rotation variants, or symbol maps for valid multi-layer targets.

## Scope

Remove hard rejection for multi-layer codes (up to four layers). Deliver per-layer analysis output consistent with `MAX_PATTERN_FAMILY_LAYERS = 4`.

## Non-goals

- Restoring removed `PatternCatalogRepository` DB macro lookup
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family)
- Changing `pattern_signature` normalization rules

## Implementation Plan

1. Remove or replace the single-layer-only guard in `analyze_pattern_lab_shape` (lines ~76–82 in `pattern_lab_service.py`).
2. Split colon-separated codes and analyze each layer using existing `explain_pattern_family_mismatch` layer-walking logic.
3. Return structured per-layer results (canonical code, structural signature, rotation variants, symbol map).
4. Ensure single-layer codes retain current behavior.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py` (reference)
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: `python manage.py check`
- manual verification: `analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu')` returns per-layer output, not error

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- UI rendering is Mid scope — service must return data shape the template can consume.
