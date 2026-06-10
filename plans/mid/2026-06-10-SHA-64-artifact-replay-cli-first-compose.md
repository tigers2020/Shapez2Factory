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

# Plan: Artifact replay CLI-first compose path

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Mid

## Problem

`compose_lab_replay_frames_from_artifact_run` prefers `build_solver_runtime_replay_frames_from_artifact_run`, which re-executes L2→L5 inside Django on every artifact replay compose. This violates the CLI-first viewer boundary in `django-residue-audit.md` (module was listed as deleted; viewer should map `replay_core.jsonl` + `complete_map` only).

Current code path (`artifact_replay_viewer_compose.py` lines 147–160): runtime compose runs first; `replay_core.jsonl` mapping is fallback only.

## Scope

- Remove or hard-disable Django in-process L2–L5 re-execution.
- Make `compose_lab_replay_frames_from_artifact_run` use `replay_core.jsonl` + `complete_map` mapper as sole compose path.
- If overlay-capable frames need runtime assembly, derive from persisted artifact fields — not layer re-run.
- Extend architecture gates for `django_apps/asteroid_lab/services/artifact_*compose*.py`.

## Non-goals

- Changing CLI stack execution or artifact write format (SHA-36).
- Rewriting `solver_runtime_assembler.py` unless required for artifact-only compose.
- L3/L5 algorithm performance tuning.

## Implementation Plan

1. Delete or gate `artifact_runtime_replay_compose.py` per residue audit; remove import from `artifact_replay_viewer_compose.py`.
2. Refactor `compose_lab_replay_frames_from_artifact_run` to return artifact-mapped frames directly (existing `_timeline_frame_from_core_record` path).
3. If overlay frames are required for renderability, enrich from persisted artifact JSON (layer summaries, complete_map) without calling `execute_layer_02_*` / `run_layer_03_*` / `run_layer_04_*` / `run_layer_05_*`.
4. Add architecture test in `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` (or sibling) banning `shapez2_factory.application.asteroid_lab.layers.*.run` imports in `artifact_*compose*.py`.
5. Add regression asserting compose module AST has no solver execution imports.
6. Update `test_artifact_replay_viewer_compose.py` to assert artifact-only path; remove runtime recompose expectations.
7. Run `pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` (delete or hard-disable)
- `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py`
- `tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md` (update if drift)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py tests/unit/asteroid_lab/test_artifact_replay_viewer_compose.py -v`
- build: `python manage.py check`
- manual verification: Load Lab replay page for indexed artifact; confirm no multi-second solver spans in perf trace.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Runtime compose may have produced richer overlay frames than artifact mapping; verify UI renderability after removal (related SHA-37, SHA-38 cache validity).
- `django-residue-audit.md` already claims module deleted — code drift confirms SHA-64 is valid.
- Perf span tests may need Low-plan updates.
