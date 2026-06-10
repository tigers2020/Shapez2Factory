---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Align Lab page context replay cache guard with lazy endpoint

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` accepts composed replay frames when renderable only, but never checks `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint requires both, causing SSR vs lazy-load disagreement.

## Scope

Align `build_asteroid_lab_page_context` cache hit logic with `public_pages.py`: require `is_cache_summary_valid` before using composed cache; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring entire replay compose pipeline.
- Broad replay schema version migration tooling.

## Implementation Plan

1. Read `asteroid_lab_page_context.py` cache-hit branch (lines ~260–272) and `public_pages.py` lazy endpoint guard (lines ~601–605).
2. Import `is_cache_summary_valid` from `lab_replay_persisted_cache.py` into page context builder.
3. Gate cache hit: renderable AND `is_cache_summary_valid(summary)` AND existing stale L3 thin-cache rules.
4. On miss, recompose and persist fresh frames (mirror lazy endpoint).
5. Add test: manifest without `lab_replay_cache_schema_version` — page context recomposes, matching lazy endpoint (`test_artifact_first_replay` pattern).
6. Run `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (read-only reference)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check django_apps/web/ django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src`
- tests: artifact first replay + page context tests
- build: N/A
- manual verification: Lab SSR and lazy JSON show same replay after schema bump scenario

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-38 loader-level fix may overlap — coordinate to avoid duplicate work.
