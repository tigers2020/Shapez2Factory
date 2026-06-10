---
linear_issue: SHA-66
title: Layer post-summary log retention is non-deterministic (mtime-only sort prunes wrong runs)
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document layer post-summary retention ordering contract (SHA-66 Low)

## Source Issue

- Linear: SHA-66
- Status at planning time: Todo
- Priority: Low

## Problem

Retention ordering contract is implicit in code; prior inspection log noted mtime flake under xdist. After Mid fix lands, operators and future maintainers need a short explicit contract.

## Scope

Document retention ordering contract in module docstring or observability notes. Optional: add integration note to `daily-project-inspection-log.md` once fixed.

## Non-goals

- Changing retention behavior (handled in Mid plan)
- Full observability schema documentation rewrite

## Implementation Plan

1. After Mid plan implementation merges, add 2–4 line docstring note on `_prune_old_runs` describing sort key: `(st_mtime, directory_name)` ascending; oldest pruned first; keeps newest `max_runs`.

2. Optionally append resolved note to `docs/agent-workflows/daily-project-inspection-log.md` under the SHA-66 / mtime flake entry with fix summary and validation command.

3. No code behavior change in this plan.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (docstring only)
- `docs/agent-workflows/daily-project-inspection-log.md` (optional note)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- typecheck: n/a (docs only unless docstring edit)
- tests: none required
- build: n/a
- manual verification: read docstring for clarity

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional polish; defer if Mid PR is time-constrained.
- Inspection log update should mark issue resolved, not duplicate open findings.
