---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Mocked render-failure test for graph preview warm API

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Mid

## Problem

`tests/integration/web/test_graph_preview_warm.py` covers auth and cache_key mismatch only. No test asserts failed render returns `ok: false`.

## Scope

Add integration/unit regression asserting mocked `PlaywrightPngGraphPreviewRenderer.render` returning `image_url=None` yields `ok: false` and non-empty error detail.

## Non-goals

- SHA-17 renderer instance reuse fix
- Changing renderer internals

## Implementation Plan

1. Read `tests/integration/web/test_graph_preview_warm.py`.
2. Mock `PlaywrightPngGraphPreviewRenderer.render` to return `GraphPreview(alt_text="x", image_url=None)`.
3. POST warm endpoint as staff user; assert `ok is False` and error detail present.
4. Add complementary test that successful mock still returns `ok: true`.
5. Run `pytest tests/integration/web/test_graph_preview_warm.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_graph_preview_warm.py`
- `django_apps/web/views/staff_shared.py` (implementation from High plan)

## Validation Plan

- lint: `ruff check tests/integration/web/test_graph_preview_warm.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Integration test with mocked renderer failure
- [ ] Failed PNG render returns `ok: false` with stable error detail
- [ ] Successful render path unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Mock patch target path must match view import site.
