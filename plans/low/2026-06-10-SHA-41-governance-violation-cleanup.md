---
linear_issue: SHA-41
title: CI never runs scripts/check_governance.ps1 required by AGENTS.md governance acceptance
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Governance violation cleanup (SHA-41 Low)

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Low

## Problem

Enabling CI governance acceptance (Mid plan) may surface pre-existing violations: `AGENTS.md` or `.cursor/rules/*.mdc` files exceeding line limits, missing Hermes handoff markers, or stale validation command references. Mid plan explicitly excludes fixing current violations; this Low plan tracks remediation so the new gate can pass on `master`.

## Scope

- Audit and fix pre-existing governance violations reported by `scripts/check_governance.ps1`.
- Split oversized routers per AGENTS.md guidance (thin routers ≤75 lines; detail in `docs/agent-workflows/`).

## Non-goals

- Adding CI governance job (Mid plan).
- Changing governance line limits or acceptance rules.
- Unrelated router content rewrites beyond line-limit compliance.

## Implementation Plan

1. Run `pwsh -File scripts/check_governance.ps1` (or `python scripts/check_governance.py` if ported) on current `master` and capture full violation list.
2. Triage: line-count WARN (exit 0) vs hard failures per AGENTS.md (>120 root AGENTS.md, >150 nested, >75 `.mdc`).
3. For hard failures, split operational detail from `.cursor/rules/*.mdc` into `docs/agent-workflows/` and leave thin routers.
4. Restore Hermes handoff markers and validation canon references where missing.
5. Re-run governance check until exit 0 before or immediately after Mid CI gate merges.

## Files / Areas Likely Affected

- `AGENTS.md`
- `.cursor/rules/*.mdc` (violating files TBD from audit)
- `docs/agent-workflows/` (absorb split detail)
- `scripts/check_governance.ps1` (reference only)

## Validation Plan

- lint: N/A for governance file splits
- typecheck: N/A
- tests: `pwsh -File scripts/check_governance.ps1` — must exit 0
- build: N/A
- manual verification: `scripts/check_governance.ps1` passes locally and in CI after Mid gate enabled

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Splitting routers may change agent behavior if detail moved incorrectly — preserve behavior-changing rules over formatting.
- Coordinate with Mid plan: cleanup PR may need to land before or atomically with CI gate to avoid blocking all merges.
