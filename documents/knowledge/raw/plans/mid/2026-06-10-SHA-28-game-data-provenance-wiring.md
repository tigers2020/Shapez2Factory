---
linear_issue: SHA-28
title: Subprocess solver runtime discards game_data_provenance; artifacts record stub catalog provenance
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire game_data_provenance through subprocess to artifact ingest

## Source Issue

- Linear: SHA-28
- Status at planning time: Todo
- Priority: Mid

## Problem

Django builds `GameDataSnapshotProvenance` but subprocess/CLI discards it. Artifacts record stub `{"source": "cli_snapshot_file"}`; `SolverRun` ingest inherits stub.

## Scope

Pass Django provenance → subprocess request → CLI manifest → ingest persistence. Use or remove unused `CATALOG_SLICE_*` error codes.

## Non-goals

- SHA-13 empty-row export fix (related, separate).
- SHA-22 gene_template_source (related, separate).

## Implementation Plan

1. Add serialized provenance to `SolverSubprocessRequest` (or equivalent).
2. Update `enqueue_solver_run_for_project` / `_run_subprocess_runtime_for_project` pass-through (stop deleting param).
3. Update `asteroid_solve.py` to write `ArtifactManifest.game_data_provenance` from request.
4. Verify ingest persists provenance on `SolverRun`.
5. Add regression test: HTTP run-solver → manifest `catalog_slice_hash` matches Django build.
6. Optional: enable `CATALOG_SLICE_REQUIRED` fail-closed per spec.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- tests under `tests/unit/asteroid_lab/`

## Validation Plan

- tests: new regression + existing artifact tests
- manual verification: manifest provenance not stub after run

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate ordering with SHA-22 provenance fields.
