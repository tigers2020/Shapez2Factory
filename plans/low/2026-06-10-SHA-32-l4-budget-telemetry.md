---
linear_issue: SHA-32
title: L4 inner fill ignores LayerBudgetContext during routeable inner group placement
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L4 budget telemetry and logging polish (SHA-32 Low)

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority budget polling lands, optional telemetry can help diagnose budget exhaustion during L4 routeable inner group placement.

## Scope

Budget polling instrumentation and logging improvements for L4 placement phases.

## Non-goals

- New observability infrastructure or external metrics sinks.
- Changing budget allocation policy.

## Implementation Plan

1. After Mid plan lands, review existing layer budget logging in stack_runner or layer modules.
2. Add debug-level log or replay event when `place_routeable_inner_groups` exits early due to budget exhaustion.
3. Optionally include remaining budget in layer summary metadata if schema supports it.
4. Document budget early-exit behavior in layer module docstring.

## Files / Areas Likely Affected

- L4 inner pattern fill module (same as Mid plan)
- TBD — replay/layer summary types if metadata extended

## Validation Plan

- lint: spot-check changed module
- typecheck: spot-check
- tests: existing layer tests still pass
- build: N/A
- manual verification: Log output visible on budget early-exit in dev run

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion.
- Replay schema changes may need contract review — prefer logging-only if uncertain.
