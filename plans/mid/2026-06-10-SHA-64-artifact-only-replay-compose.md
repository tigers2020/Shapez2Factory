---
linear_issue: SHA-64
title: Lab artifact replay compose re-executes L2-L5 solver stack from Django
priority: Mid
labels:
  - bug
  - performance
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Remove Django in-process L2–L5 re-execution from artifact replay compose

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Mid

## Problem

`compose_lab_replay_frames_from_artifact_run` prefers `build_solver_runtime_replay_frames_from_artifact_run`, which re-executes the full L2→L5 solver stack inside Django on every artifact replay compose. This violates the CLI-first viewer boundary in `django-residue-audit.md`. Lab page loads can trigger minutes of server-side solver work even though `replay_core.jsonl` and `complete_map` are already persisted.

## Scope

- Remove or hard-disable the Django in-process L2–L5 re-execution path.
- Make `compose_lab_replay_frames_from_artifact_run` use `replay_core.jsonl` + `complete_map` enrichment as the primary/only compose path.
- Extend architecture import gates to cover `artifact_*compose*` viewer services.

## Non-goals

- Changing CLI stack execution or artifact write format (SHA-36).
- Rewriting `solver_runtime_assembler.py` unless required for artifact-only compose.
- Performance tuning of L3/L5 algorithms.

## Implementation Plan

1. **Confirm artifact-only path is renderable**
   - Run existing `test_artifact_replay_viewer_compose.py` cases; verify `_timeline_frame_from_core_record` + `map_view_from_complete_map` produces `lab_replay_frames_are_renderable` frames for committed fixtures.
   - Document any gap where runtime compose was masking missing `map_view` data.

2. **Remove runtime compose preference**
   - In `artifact_replay_viewer_compose.py`, delete import and call to `build_solver_runtime_replay_frames_from_artifact_run`.
   - Use artifact mapper path (lines 162–168) as sole compose when manifest + files valid.
   - Set `inspector.replay_source` to `artifact_replay_core` consistently.

3. **Delete or disable `artifact_runtime_replay_compose.py`**
   - Per `django-residue-audit.md`, remove module or replace with stub raising `NotImplementedError` if external imports remain.
   - Grep for `artifact_runtime_replay_compose` and update callers/tests.

4. **Architecture regression gate**
   - Extend `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` (or sibling) to ban imports of `shapez2_factory.application.asteroid_lab.layers.*.run` from `django_apps/asteroid_lab/services/artifact_*compose*.py`.
   - Add test asserting `artifact_runtime_replay_compose` is not importable or is empty stub.

5. **Update related tests**
   - Fix `test_lab_replay_compose_perf_spans.py` if it instruments deleted span.
   - Re-run `test_artifact_replay_viewer_compose.py`, `test_lab_island_raw_coord_frame.py`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` (delete/disable)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md` (reference)
- `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py`
- `tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py`
- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py -v`
- build: `python manage.py check`
- manual verification: Lab page load for artifact run does not spike CPU / long request time

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Runtime compose may have been workaround for incomplete `replay_core` overlay data — verify against SHA-36/37/38 related issues before delete.
- Overlay frames derived only from persisted fields may lack fidelity; document tradeoff in PR.
- Coordinate with SHA-21 deserialization guard if compose path touches frame parsing.
