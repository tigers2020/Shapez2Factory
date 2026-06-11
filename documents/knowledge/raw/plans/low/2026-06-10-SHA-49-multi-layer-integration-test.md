---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Integration regression for multi-layer Pattern Lab GET

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Low

## Problem

No integration test covers colon-separated multi-layer shape codes on the Pattern Lab page. Single-layer GET is tested; multi-layer hard rejection is untested at HTTP layer.

## Scope

Add integration test asserting GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` returns 200 with per-layer signature output and no "Analysis failed" / single-layer-only error message.

## Non-goals

- Service-layer unit tests (High plan)
- Template markup refactor (Mid plan)
- Testing >4 layer rejection at HTTP layer (optional; unit test sufficient)

## Implementation Plan

1. Add test to `tests/integration/web/test_pattern_lab.py`:

```python
@override_settings(LANGUAGE_CODE="en")
def test_pattern_lab_page_shows_multi_layer_signatures() -> None:
    response = Client().get(
        reverse("web:pattern-lab"),
        {"code": "CuCuCuCu:CuCuCuCu"},
        **_EN_HEADERS,
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "CuCuCuCu:CuCuCuCu" in content
    assert "AAAA" in content
    assert "Analysis failed" not in content
    assert "single-layer shape codes only" not in content
```

2. If Mid plan adds "Layer" headings, strengthen assertion:

```python
assert "Layer 0" in content or "Layer 1" in content
```

3. Run targeted integration test:

```bash
pytest tests/integration/web/test_pattern_lab.py::test_pattern_lab_page_shows_multi_layer_signatures -v
```

4. Run full pattern lab integration module:

```bash
pytest tests/integration/web/test_pattern_lab.py -v
```

5. Confirm existing `test_pattern_lab_page_shows_signature_without_macro_candidates` still passes (single-layer regression).

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- lint: `ruff check tests/integration/web/test_pattern_lab.py`
- typecheck: `mypy tests/integration/web/test_pattern_lab.py` (if in scope)
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: not applicable
- manual verification: optional duplicate of GET check

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test depends on High + Mid plans landing first; run order: High → Mid → Low.
- English-only assertions match existing integration test style (`LANGUAGE_CODE="en"`).
