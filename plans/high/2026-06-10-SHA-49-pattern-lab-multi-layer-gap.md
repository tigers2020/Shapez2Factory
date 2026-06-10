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

# Plan: Enable Pattern Lab analysis for valid multi-layer shape codes

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: High

## Problem

Pattern Lab (`analyze_pattern_lab_shape`) hard-rejects any multi-layer shape code (`:`-separated), but the same codebase already supports per-layer pattern-family checks for up to four layers via `explain_pattern_family_mismatch`. Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that are valid in recipe graphs.

## Scope

Remove the hard rejection for multi-layer codes up to the existing four-layer contract and deliver per-layer analysis output in Pattern Lab.

## Non-goals

- Restoring removed `PatternCatalogRepository` DB macro lookup.
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family).
- Changing `pattern_signature` normalization rules.

## Implementation Plan

1. Reproduce: `analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu')` returns hard error; `explain_pattern_family_mismatch` succeeds for same input.
2. Remove or narrow the single-layer-only guard in `pattern_lab_service.py` (lines ~76–82) to allow up to `MAX_PATTERN_FAMILY_LAYERS` (4).
3. Delegate per-layer analysis to existing `explain_pattern_family_mismatch` layer-walking logic.
4. Verify single-layer codes behave identically after change.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `django_apps/shapez_solver/templates/shapez_solver/pattern_lab.html` (Mid plan)
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: N/A
- manual verification: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows per-layer output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Multi-layer codes up to four layers analyze without hard rejection.
- [ ] No change to single-layer behavior.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- UI rendering for per-layer blocks tracked in Mid plan; service and template should land in same PR.
