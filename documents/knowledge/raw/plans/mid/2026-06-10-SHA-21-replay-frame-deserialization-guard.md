---
linear_issue: SHA-21
title: Artifact replay timeline compose crashes on malformed frame (missing deserialization guard)
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Per-frame deserialization guard for artifact replay compose path

## Source Issue

- Linear: SHA-21
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_lab_replay_frames_for_project` artifact path deserializes frames without per-frame try/except. Malformed frame raises `ReplayTimelineDeserializationError` → HTTP 500. Config-json runtime path already has guards.

## Scope

Mirror config-json per-frame error handling in artifact compose path; add regression test.

## Non-goals

- Do not fix SHA-9 ingest issues.
- Do not change replay schema.

## Implementation Plan

1. Compare artifact compose path vs `_solver_runtime_timeline_frames_for_run` in `lab_replay_timeline_payload.py`.
2. Extract shared per-frame deserialize helper with skip-on-error behavior.
3. Apply to `build_lab_replay_frames_for_project` artifact branch.
4. Add unit test: unknown `event_type` frame skipped or surfaced without 500.
5. Run `pytest tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- `django_apps/asteroid_lab/replay/timeline_serialization.py`
- `tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Skipped frame diagnostics in UI is Low follow-up.
