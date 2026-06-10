---
linear_issue: SHA-13
title: game_data snapshot export allows empty EVTC/mining rows (fail-open before CLI)
priority: Mid
labels:
  - bug
  - priority:mid
status: in_progress
created_by: todo-plan-automation
---

# Plan: Fail-closed game_data snapshot export for missing EVTC/mining rows

## Source Issue

- Linear: SHA-13
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_game_data_snapshot_payload` exports schema-valid snapshot when ORM has zero active EVTC/fluid/mining rows. L2 fails later with `MISSING_EVTC_ROW` instead of failing at Django export boundary.

## Scope

Reject export when required active rows missing; HTTP `run_solver` → 400; management export command fails.

## Non-goals

- No schema/hash changes.
- No L3/L5 solver changes.

## Implementation Plan

1. Define minimum required active rows per BA-8 in `game_data_snapshot_export.py`.
2. Add `GameDataSnapshotExportError` when counts are zero.
3. Wire `public_pages._run_solver_post_traced` to return 400 on export error.
4. Wire `export_game_data_snapshot` command to fail with non-zero exit.
5. Add `tests/unit/game_data/` coverage.
6. Run targeted pytest.

## Files / Areas Likely Affected

- `django_apps/game_data/services/game_data_snapshot_export.py`
- `django_apps/game_data/services/exterior_transport_capacity.py`
- `django_apps/web/views/public_pages.py`
- `tests/unit/asteroid_lab/layers/test_layer_02_capacity.py` (reference)
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` (§7 BA-8)

## Validation Plan

- tests: new unit tests + `pytest tests/unit/game_data/ -v` if present
- lint: `ruff check django_apps/game_data/`
- manual verification: empty ORM DB export fails before CLI invoke

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-28 provenance wiring is separate.
