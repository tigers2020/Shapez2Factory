---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Low
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Replay schema migration tooling (SHA-37 Low)

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Low

## Problem

Cache validity guards (Mid plan) will reject stale composed replay when `lab_replay_cache_schema_version` is missing or outdated. Without migration tooling, operators may face bulk invalid caches after schema bumps, requiring manual recompose for many SolverRun rows.

## Scope

- Design optional migration/backfill tooling when `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION` increments.
- Document operator runbook for cache invalidation and bulk recompose.

## Non-goals

- Page-context cache validity guard (Mid plan).
- Loader path unification (SHA-38).
- Changing artifact-jsonl first authority semantics.

## Implementation Plan

1. Document schema bump procedure in `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` or adjacent ops doc, referencing `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`.
2. Evaluate Django management command to invalidate or recompose stale `lab_replay_payload_json` rows (filter by manifest summary schema version).
3. Add dry-run mode listing affected SolverRun IDs before bulk recompose.
4. Cross-link SHA-38 loader fix so migration targets consistent validity contract.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- TBD — `django_apps/asteroid_lab/management/commands/` recompose/backfill command
- `docs/agent-workflows/` or asteroid lab ops doc (if exists)

## Validation Plan

- lint: `ruff check` on new command module
- typecheck: spot-check new management command
- tests: unit test for dry-run row selection logic with fixture manifests
- build: N/A
- manual verification: dry-run on dev DB lists expected stale runs without writes

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Bulk recompose may re-execute solver stack (SHA-64 concern) — migration must prefer artifact-jsonl compose where possible.
- Defer until next schema version bump unless stale cache volume is high.
