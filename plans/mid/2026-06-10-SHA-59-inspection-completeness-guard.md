---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Mid
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Raise _INSPECTION_EXPECTED_FRAMES and add regression test for trim-reconstruction scenario

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode frame plus four cleanup/reconstruction frames, but `record_decoded_snapshot_frames` appends two decode frames. The constant is stale and the count-only guard allows truncated replays. Regression coverage for the trim-reconstruction scenario is missing.

## Scope

Update `_INSPECTION_EXPECTED_FRAMES` to the documented minimum (≥6) and add a pytest that builds a full replay, trims reconstruction frames to five, and asserts the second `build_initial_replay_for_map_input` call returns `failed` unless `force=True`.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` from `5` to `6` in `replay_pipeline_service.py` and fix the stale comment (`decode (2) + cleanup (3) + reconstruction (≥1)` or equivalent accurate wording).
2. Add helper `_inspection_replay_is_complete` (or share with High plan) that checks for at least one reconstruction `event_type` in track frames.
3. Write failing test `test_build_initial_replay_rejects_partial_track_without_reconstruction`:

```python
@pytest.mark.django_db
def test_build_initial_replay_rejects_partial_track_without_reconstruction() -> None:
    code = _encode_v4_copy(_minimal_root(version=31))
    dto = project_service.create_project_from_copy_code(code, source_label="partial")
    r1 = build_initial_replay_for_map_input(dto.map_input_id)
    assert r1.status == "ok"
    assert r1.replay_frame_count >= 6

    recon_types = frozenset({
        et.EVENT_TYPE_RECONSTRUCTION_BEGIN,
        et.EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
        et.EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL,
        et.EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED,
        et.EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED,
        et.EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED,
        et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
    })
    frames = list(
        m.ReplayFrame.objects.filter(replay_track_id=r1.replay_track_id).order_by("frame_index", "id")
    )
    keep = [f for f in frames if str(f.frame_payload.get("event_type") or "") not in recon_types]
    assert len(keep) == 5  # decode x2 + cleanup x3

    m.ReplayFrame.objects.filter(replay_track_id=r1.replay_track_id).delete()
    m.ReplayFrame.objects.bulk_create(
        [m.ReplayFrame(replay_track_id=r1.replay_track_id, frame_index=i, frame_payload=f.frame_payload) for i, f in enumerate(keep)]
    )

    r2 = build_initial_replay_for_map_input(dto.map_input_id)
    assert r2.status == "failed"
    assert "Incomplete inspection replay" in r2.error_message
    assert r2.replay_frame_count == 5

    r3 = build_initial_replay_for_map_input(dto.map_input_id, force=True)
    assert r3.status == "ok"
    assert r3.replay_frame_count >= 6
```

4. Run `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py::test_build_initial_replay_rejects_partial_track_without_reconstruction -v` — expect FAIL before fix, PASS after.
5. Run full file: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.
6. Confirm `test_build_initial_replay_idempotent_without_force` still passes (complete replay short-circuit unchanged).

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (read-only: `record_decoded_snapshot_frames` emits 2 decode frames)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (read-only: cleanup frame emission)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/replay_pipeline_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] `_INSPECTION_EXPECTED_FRAMES` raised to ≥6 with accurate comment.
- [ ] Regression test for trim-reconstruction → second call fails without `force=True`.
- [ ] Complete replays still short-circuit idempotently.
- [ ] `force=True` rebuild path unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Exact reconstruction `event_type` checklist may need alignment with `event_types.py` canonical set; prefer importing constants over string literals.
- If trim leaves exactly 5 frames but a stray reconstruction marker remains, test setup must delete all recon types explicitly.
