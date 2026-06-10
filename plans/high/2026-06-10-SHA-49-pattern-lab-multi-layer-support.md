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

# Plan: Enable Pattern Lab multi-layer shape analysis

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: High

## Problem

`analyze_pattern_lab_shape` hard-rejects any multi-layer shape code (`:`-separated) at lines 76–82 of `pattern_lab_service.py`, returning `"Pattern Lab currently supports single-layer shape codes only."` Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that recipe graph validation already accepts (up to four layers via `MAX_PATTERN_FAMILY_LAYERS`).

## Scope

Remove the single-layer hard rejection and return per-layer analysis for colon-separated codes up to `MAX_PATTERN_FAMILY_LAYERS` (4). Preserve existing single-layer behavior.

## Non-goals

- Restoring `PatternCatalogRepository` DB macro lookup.
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family).
- Changing `pattern_signature` normalization rules.

## Implementation Plan

1. Extend `PatternLabAnalysis` or introduce a per-layer result type (e.g. `PatternLabLayerAnalysis`) holding canonical code, signature, symbol map, rotation variants per layer.
2. In `analyze_pattern_lab_shape`, when `not target_shape.is_single_layer()`:
   - Reject only if `len(target_shape.layers) > MAX_PATTERN_FAMILY_LAYERS`.
   - Walk each layer; build per-layer canonical 8-char code, signature, symbol map, rotation variants (reuse `_build_symbol_map`, `_build_rotation_variants`, `pattern_signature`).
3. Return structured multi-layer result instead of `_error_result` for valid ≤4-layer codes.
4. Keep parse-error and empty-input paths unchanged.
5. Add unit test: `analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu')` returns no error and two layer blocks.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: N/A
- manual verification: `python -c` repro from issue spec returns analysis, not error string

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `PatternLabAnalysis` is currently flat; multi-layer may need dataclass extension or nested tuple — align with view/template expectations (Mid plan).
- DB macro candidates are signature-based per layer; define whether candidates attach per layer or top-level only.
