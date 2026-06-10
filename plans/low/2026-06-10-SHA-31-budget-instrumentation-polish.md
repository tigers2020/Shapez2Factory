---
linear_issue: SHA-31
title: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L3 Phase B budget polling instrumentation polish (SHA-31 Low)

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority Phase B budget polling lands, observability for budget-truncated expansions may be incomplete: `budget_skipped_count` alone may not explain which anchors/profiles were skipped or how much stack time L3 consumed before yielding.

## Scope

- Optional logging/observability polish for Phase B budget interrupts.
- Document budget skip semantics in layer post summary or `Layer03ExpansionMetrics` if gaps remain after Mid fix.

## Non-goals

- Changing budget enforcement behavior (Mid plan owns that).
- New metrics consumed by solver heuristics or replay input.

## Implementation Plan

1. After Mid fix merges, review `build_layer03_observability` output for budget-truncation visibility.
2. If `layer_post_summary` lacks budget skip signal, add `budget_skipped_count` (and optional `budget_interrupted: true`) to L3 post-summary row — mirror L5 `greedy.py` budget interrupt pattern.
3. Add debug-level log line when Phase B exits early due to budget (anchor index, profiles completed, skipped probe count).
4. Update `docs/agent-workflows/daily-project-inspection-log.md` entry for SHA-31 when resolved.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer03_observability.py`
- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- TBD: only if Mid fix leaves observability gaps

## Validation Plan

- lint: `ruff check .` (touched files only)
- typecheck: `mypy django_apps config src` (if types change)
- tests: extend existing layer post summary tests if new fields added
- build: `python manage.py check`
- manual verification: inspect layer post summary JSON after tight-budget solver run

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Defer until Mid plan completes; may be unnecessary if `budget_skipped_count` + existing metrics suffice.
- Depends on Mid plan: `plans/mid/2026-06-10-SHA-31-l3-phase-b-budget-polling.md`.
