---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Other frontend bundle drift gates (deferred)

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low (deferred from SHA-44 non-goals)

## Problem

SHA-44 mid scope covers `app.css` only. Related committed-artifact drift gaps remain in separate issues: graph-layout bundles (SHA-35), recipe-graph-editor Vitest/build (SHA-40), locale catalogs (SHA-42). Pytest substring guards in `test_asteroid_lab_ui_strings.py` only cover a few lab classes.

## Scope

Track only. No implementation in SHA-44.

## Non-goals

- Unified frontend static-asset CI job bundling all targets.
- Expanding pytest substring guards to full CSS rebuild coverage.

## Implementation Plan

1. Complete SHA-44 mid plan (`build:css` gate).
2. Track SHA-35, SHA-40, SHA-42 independently.
3. Consider unified frontend CI pattern after individual gates land.

## Files / Areas Likely Affected

- SHA-35: `frontend/graph_layout/`
- SHA-40: `frontend/recipe_graph_editor/`
- SHA-42: `locale/ko/LC_MESSAGES/`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Deferred items remain out of SHA-44 mid scope.
- [ ] Related issues stay tracked separately.

## Risks / Open Questions

- Operators may assume SHA-44 fixes all frontend drift; docs should clarify scope.
