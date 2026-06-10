# django_apps/asteroid_lab AGENTS.md

## Scope

Asteroid Lab Django-side map input, run registry, artifact ingest, replay/viewer adapters, cache mirrors, and management wrappers.

## Authority

- Runtime path: Django request -> game-data snapshot -> CLI subprocess -> finalized artifact -> DB index/cache -> replay/viewer.
- Solver execution belongs to `src/shapez2_factory/`; Django may invoke, index, ingest, and display.
- Current canon/spec/ADR beats old plans, deleted docs, and agent memory.

## Rules

- Replay/artifacts are output-only; do not use them as algorithm input.
- DB fields mirror artifact state; do not rerun L2/L3/L4/L5 in viewer or cache paths.
- Keep `solver_runtime_entry.py`, subprocess runner, artifact ingest, and persisted replay cache boundaries explicit.
- Schema or replay changes need versioning, migration notes, and regression tests.
- Coordinate frame changes must preserve island-local copy JSON boundaries unless canon changes.

## Verify

- Focused tests under `tests/unit/asteroid_lab/`, `tests/unit/asteroid_lab/replay/`, or matching integration tests.
- Solver smoke when runtime path changes: `python manage.py run_solver --slug <slug>`.
