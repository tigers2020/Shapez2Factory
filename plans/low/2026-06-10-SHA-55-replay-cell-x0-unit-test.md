---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Optional view-level unit test for replay cell POST at x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

Integration tests cover the full create→frame→POST path but a lightweight view unit test with a minimal mocked `ReplayFrame` / serialized payload would catch regressions of the `invalid_x_zero` guard without DB solver setup.

## Scope

Add an optional unit test on `asteroid_miner_layout_replay_frame_cell` using mocked frame and serialized payload to assert `x == 0` returns HTTP 200 (not `invalid_x_zero`).

## Non-goals

- Do not duplicate full integration coverage from Mid plan.
- Do not change view behavior (covered by High/Mid plans).

## Implementation Plan

1. Create or extend `tests/unit/web/test_replay_frame_cell_view.py` (new file if absent).
2. Use `django.test.RequestFactory` or `Client` with `@pytest.mark.django_db` and monkeypatch/mocker on `ReplayFrame.objects.filter().first()` and `serialize_replay_frame`.
3. Minimal serialized payload from `test_lookup_synthetic_lab_empty_inside_island_bbox_only`:
   ```python
   ser = {
       "full_map": [{"x": 0, "y": 0, "cell_kind": "space_belt"}],
       "diff": {},
       "cell_overlay_json": {},
   }
   ```
4. POST JSON `{"replay_frame_id": 1, "replay_track_id": 1, "x": 0, "y": 0}` to view; assert status 200, `ok: true`, no `error: invalid_x_zero`.
5. Run: `pytest tests/unit/web/test_replay_frame_cell_view.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_view.py` (create)
- `django_apps/web/views/public_pages.py` (test target only)

## Validation Plan

- lint: `ruff check tests/unit/web/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_replay_frame_cell_view.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] View unit test proves `x == 0` is accepted (no `invalid_x_zero`).
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mocking ORM + serializer may be brittle; skip if integration test already provides sufficient guard and team prefers fewer mocks.
