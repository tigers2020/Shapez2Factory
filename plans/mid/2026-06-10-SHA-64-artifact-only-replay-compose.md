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

# Plan: Remove Django in-process L2-L5 replay re-execution

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Mid

## Problem

`compose_lab_replay_frames_from_artifact_run` prefers `build_solver_runtime_replay_frames_from_artifact_run`, which re-executes the full L2→L5 solver stack inside Django on every artifact replay compose. This violates the CLI-first viewer boundary documented in `django-residue-audit.md`.

## Scope

Remove or gate the Django in-process L2–L5 re-execution path so Lab replay compose uses CLI artifact outputs (`replay_core.jsonl` + `complete_map` enrichment) as the primary/only solver replay source. Extend architecture gates to cover viewer services that import solver execution modules.

## Non-goals

- Changing CLI stack execution or artifact write format (SHA-36).
- Rewriting replay segment assembly in `solver_runtime_assembler.py` unless required for artifact-only compose.
- Performance tuning of L3/L5 algorithms themselves.

## Implementation Plan

1. Read `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py` and `artifact_runtime_replay_compose.py`; trace `compose_lab_replay_frames_from_artifact_run` call graph and fallback to `replay_core.jsonl` mapper.
2. Per `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md`, delete or hard-disable `artifact_runtime_replay_compose.py`; make artifact-only compose the sole path.
3. If overlay-capable frames need runtime assembly, derive from persisted artifact fields (`replay_core.jsonl`, `complete_map`, manifest) — do not import `shapez2_factory.application.asteroid_lab.layers.*.run`.
4. Add architecture test extending `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` to ban solver execution imports in `django_apps/asteroid_lab/services/artifact_*compose*.py`.
5. Add regression test asserting compose does not import layer run modules (mirror `test_replay_modules_do_not_import_solver_execution_core` pattern).
6. Update `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py` if spans change after path removal.
7. Run targeted tests: `pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py` (delete or disable)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md` (verify alignment)
- `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py`
- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- TBD — `solver_runtime_assembler.py` if overlay derivation needs adjustment

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src` (changed modules)
- tests: architecture + replay compose tests above; `powershell -File scripts/test_fast.ps1` if in scope
- build: N/A
- manual verification: Lab artifact replay page loads without triggering layer execution imports (grep/log or span absence)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlay frames may have depended on runtime re-execution — verify artifact-only path produces renderable frames for existing indexed runs.
- Related SHA-21/36/37/38 may affect compose/cache behavior; cross-link only unless blocking.
