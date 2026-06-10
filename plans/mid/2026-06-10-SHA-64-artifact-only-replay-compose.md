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

# Plan: Lab artifact replay compose re-executes L2-L5 solver stack from Django

## Source Issue

- Linear: SHA-64
- Status at planning time: In Progress (plans committed on branch `cursor/SHA-64-linear-todo-plan-writing-c060`)
- Priority: Mid

## Problem

`compose_lab_replay_frames_from_artifact_run` prefers `build_solver_runtime_replay_frames_from_artifact_run`, which re-executes the full L2→L5 solver stack inside Django on every artifact replay compose. This violates the CLI-first viewer boundary documented in `django-residue-audit.md` (module listed as deleted; viewer should map stored `replay_core.jsonl` + `complete_map` only).

## Scope

Remove or gate the Django in-process L2–L5 re-execution path so Lab replay compose uses CLI artifact outputs (`replay_core.jsonl` + `complete_map` enrichment) as the primary/only solver replay source. Extend architecture gates to cover viewer services that import solver execution modules.

## Non-goals

- Changing CLI stack execution or artifact write format (track separately under SHA-36).
- Rewriting replay segment assembly in `solver_runtime_assembler.py` unless required for artifact-only compose.
- Performance tuning of L3/L5 algorithms themselves.

## Implementation Plan

1. Delete `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` per `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md` §Removed.
2. Refactor `compose_lab_replay_frames_from_artifact_run` in `artifact_replay_viewer_compose.py` to use only the existing `replay_core.jsonl` + `complete_map` mapper (`_timeline_frame_from_core_record` / `iter_replay_core_frames`); remove the lazy import and `build_solver_runtime_replay_frames_from_artifact_run` call path (lines 147–160).
3. If overlay-capable frames still need runtime assembly, derive them from persisted artifact fields (manifest paths, `complete_map`, per-layer summaries in artifact JSON) rather than re-running `execute_layer_02_exterior_transport_plan`, `run_layer_03_rim_greedy_placement`, `run_layer_04_inner_pattern_fill`, or `run_layer_05_transport_routing`.
4. Add architecture test in `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` mirroring `test_replay_modules_do_not_import_solver_execution_core` for `django_apps/asteroid_lab/services/artifact_*compose*.py` — assert no imports from `shapez2_factory.application.asteroid_lab.layers.*.run`.
5. Extend `test_viewer_services_do_not_import_django_layer_shims` coverage or add sibling test ensuring compose services do not import solver execution `run` modules.
6. Add regression test that `compose_lab_replay_frames_from_artifact_run` returns renderable frames from fixture artifact without importing layer `run` modules (monkeypatch or AST gate).
7. Update `django-residue-audit.md` only if residue list changes; confirm deleted module stays listed under §Removed.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` (delete)
- `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py`
- `tests/unit/asteroid_lab/` (new regression for artifact-only compose)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md` (verify only)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py tests/unit/asteroid_lab/ -k "replay or compose" -v`
- build: `python manage.py check`
- manual verification: Load Lab replay page for an indexed artifact run; confirm compose completes without multi-second solver spans in server logs.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Removing runtime recompose may reduce overlay fidelity for artifacts missing `replay_core.jsonl` but with valid `complete_map`; confirm fallback behavior and user-visible empty state.
- Related cache staleness issues (SHA-37, SHA-38) may surface more often once compose is fast; out of scope unless regression appears.
- `artifact_runtime_replay_compose_ms` and per-layer compose perf spans will disappear; Low-priority test update tracked separately.
