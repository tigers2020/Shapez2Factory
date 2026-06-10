---
linear_issue: SHA-61
title: Space transport catalog — IO signature unit test coverage
priority: Mid
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add unit tests for routable tile IO signatures

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Mid

## Problem

`test_space_transport_catalog_import.py` covers Forward + lift only. No assertion that all 38 routable non-lift tiles have `io_signature` after import.

## Scope

- Curated R0 IO masks for 16 merger/splitter belt+pipe tiles (implementation in high plan).
- Unit test asserting all routable non-lift tiles have signatures.

## Non-goals

- L5 routing algorithm changes.

## Implementation Plan

1. After high plan populates masks, add `test_import_routing_allowed_tiles_have_io_signature`.
2. Assert exactly 38 routable non-lift tiles (54 total − 16 lifts) each have non-null `io_signature`.
3. Add `test_lookup_io_resolves_merger_and_splitter` for representative tile ids.
4. Run `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`

## Acceptance Criteria

- [ ] All 38 routable non-lift tiles have `io_signature` after import.
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`.

## Risks / Open Questions

- Tile count (38) must match committed game_data; verify if catalog size changes.
