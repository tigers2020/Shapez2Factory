---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: Low
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Manifest error_code schema documentation (SHA-33 Low)

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Low

## Problem

After High-priority fix, manifest `error_code` semantics for stack failures should be documented in artifact design spec.

## Scope

Manifest schema documentation updates for `error_code` on stack-failure artifacts.

## Non-goals

- Schema version bump unless required by contract change process.

## Implementation Plan

1. After High plan lands, update `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` manifest section with `error_code` population rules for stack failures.
2. Document Django ingest mapping: `error_code` + `run_success` → lifecycle status.
3. Cross-link from SHA-10 regression test docstring or checklist if applicable.

## Files / Areas Likely Affected

- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- TBD — checklist or ADR if error code enum documented separately

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Spec §manifest matches implemented finalize behavior

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan completion and final error_code enum values chosen.
