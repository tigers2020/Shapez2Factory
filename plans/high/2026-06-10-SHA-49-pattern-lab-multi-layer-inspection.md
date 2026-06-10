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
- Status at planning time: Todo
- Priority: High

## Problem

Pattern Lab (`analyze_pattern_lab_shape`) hard-rejects any multi-layer shape code (`:`-separated), but recipe graph validation already supports per-layer pattern-family checks for up to four layers via `explain_pattern_family_mismatch`. Staff cannot inspect signatures, rotation variants, or symbol maps for multi-layer targets that are valid in recipe graphs.

## Scope

Remove the single-layer hard rejection in `analyze_pattern_lab_shape` and return successful analysis for colon-separated codes with 1–4 layers, aligned with `MAX_PATTERN_FAMILY_LAYERS = 4` and `MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN = 4`.

## Non-goals

- Restoring `PatternCatalogRepository` DB macro lookup (tables dropped in migration `0009_drop_pattern_catalog_tables`)
- Wiring `validate_recipe_graph_context` into production recompute (SHA-24 family)
- Changing `pattern_signature` normalization rules
- Template/UI layout work (covered in Mid plan)

## Implementation Plan

1. Add a failing unit test `test_pattern_lab_analyzes_two_layer_shape` in `tests/unit/shapez_solver/test_pattern_lab_service.py`:

```python
def test_pattern_lab_analyzes_two_layer_shape() -> None:
    analysis = analyze_pattern_lab_shape("CuCuCuCu:CuCuCuCu")

    assert analysis.error == ""
    assert analysis.canonical_code == "CuCuCuCu:CuCuCuCu"
    assert len(analysis.layers) == 2
    assert analysis.layers[0].signature == "AAAA"
    assert analysis.layers[1].signature == "AAAA"
```

2. Run `pytest tests/unit/shapez_solver/test_pattern_lab_service.py::test_pattern_lab_analyzes_two_layer_shape -v` and confirm FAIL (current hard rejection).

3. Introduce `PatternLabLayerAnalysis` dataclass in `pattern_lab_service.py` with fields: `layer_index`, `layer_code`, `canonical_code`, `signature`, `symbol_map`, `rotation_variants`, `distinct_part_count`, `db_candidates`.

4. Extend `PatternLabAnalysis` with `layers: tuple[PatternLabLayerAnalysis, ...] = ()`. Keep existing top-level fields populated from layer 0 for single-layer codes so current callers/tests remain unchanged.

5. Replace lines 76–82 hard rejection with layer-count guard:

```python
layer_count = len(target_shape.layers)
if layer_count > MAX_PATTERN_FAMILY_LAYERS:
    return _error_result(
        normalized_input,
        f"multi-layer shape exceeds maximum of {MAX_PATTERN_FAMILY_LAYERS} layers",
        canonical_code=canonical_code,
        warnings=tuple(warnings),
    )
```

6. For each layer in `target_shape.layers`, build per-layer analysis by reusing existing helpers:

```python
layer_code = "".join(f"{part.kind}{part.color}" for part in layer.quadrants)
layer_canonical = shape_from_pattern(parse_shape_code_list(layer_code)[0]).canonical_code
signature = pattern_signature(layer_canonical)
```

7. Populate `layers` tuple; for single-layer input, also set top-level `signature`, `symbol_map`, `rotation_variants`, `distinct_part_count`, `db_candidates` as today.

8. Re-run unit tests including existing `test_pattern_lab_analyzes_signature_without_db_candidates` to confirm single-layer behavior unchanged.

9. Run repro from issue and confirm no error string:

```bash
python3 -c "from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape; a=analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu'); print(a.error); print(len(a.layers))"
```

Expected: empty error, `2`.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/pattern_lab_service.py`
- `tests/unit/shapez_solver/test_pattern_lab_service.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_solver/services/pattern_lab_service.py`
- typecheck: `mypy django_apps/shapez_solver/services/pattern_lab_service.py`
- tests: `pytest tests/unit/shapez_solver/test_pattern_lab_service.py -v`
- build: not applicable
- manual verification: repro command above returns empty error and two layer entries

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Top-level `PatternLabAnalysis` fields for multi-layer: plan keeps layer-0 mirror for backward compatibility; template will read `layers` (Mid plan).
- DB macro candidate lookup per layer may return duplicates; acceptable for staff inspection workflow.
