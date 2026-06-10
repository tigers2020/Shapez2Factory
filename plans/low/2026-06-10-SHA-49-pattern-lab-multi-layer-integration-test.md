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

# Plan: Pattern Lab multi-layer integration regression

## Source Issue

- Linear: SHA-49
- Status at planning time: In Progress
- Priority: Low

## Problem

Integration coverage only exercises single-layer GET (`CuRuSuSu`). No HTTP regression guards against reintroducing the multi-layer hard rejection in the staff Pattern Lab page.

## Scope

Add integration test for colon-separated multi-layer code GET expecting per-layer output, not the single-layer-only error.

## Non-goals

- E2E browser automation (Playwright) unless integration test insufficient
- Testing `explain_pattern_family_mismatch` (already covered in unit tests)

## Implementation Plan

1. Open `tests/integration/web/test_pattern_lab.py`.
2. Add `test_pattern_lab_page_shows_multi_layer_per_layer_signatures`:
   - GET `reverse("web:pattern-lab")` with `{"code": "CuCuCuCu:CuCuCuCu"}` and English headers.
   - Assert `response.status_code == 200`.
   - Assert `"Analysis failed"` not in content (or `analysis.error` path not taken).
   - Assert both layer canonical fragments or per-layer headings present (e.g. `CuCuCuCu`, `Layer`, signature `AAAA` or equivalent).
   - Assert single-layer-only error string absent: `"supports single-layer shape codes only"`.
3. Optionally add negative case: five-layer code shows layer-limit error (if exposed via UI).
4. Run `pytest tests/integration/web/test_pattern_lab.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- lint: `ruff check tests/integration/web/test_pattern_lab.py`

## Acceptance Criteria

- [ ] Integration regression added for multi-layer GET.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Test assertions depend on exact template copy from Mid plan — align expected strings with final layer headings.
