---
linear_issue: SHA-9
title: Artifact ingest indexes COMPLETED SolverRun with empty solver_summary when paths/hash validation decoupled
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Artifact ingest fail-closed for declared solver_summary paths

## Source Issue

- Linear: SHA-9
- Status at planning time: Todo
- Priority: Mid

## Problem

`ingest_artifact_for_project` can index `COMPLETED` runs with empty `solver_summary_json` when manifest declares `paths.solver_summary` but the file is missing or not in `content_hashes`.

## Scope

Require declared path keys to exist on disk and match `content_hashes` before COMPLETED indexing; raise `ArtifactIngestError` instead of silent `{}`.

## Non-goals

- Do not change CLI `AtomicArtifactWriter` hash rules.
- Do not fix SHA-12 reconcile leak (separate issue).

## Implementation Plan

1. Audit `django_apps/asteroid_lab/services/artifact_ingest.py` and `artifact_manifest_reader.py` for `_dict_json_file` silent-empty behavior.
2. Define required manifest path keys (minimum `solver_summary`).
3. For each required key: verify relpath exists under artifact dir and appears in `content_hashes`.
4. Replace silent `{}` with `ArtifactIngestError` when declared but missing/unhashed.
5. Add unit test: paths declare `solver_summary`, empty hashes, missing file → raise, no DB row.
6. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `django_apps/asteroid_lab/services/artifact_manifest_reader.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` (§2/§5 reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- build: N/A
- manual verification: Repro from issue (paths + empty hashes + missing file)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-12 handles reconcile exception path; coordinate error codes if needed.
