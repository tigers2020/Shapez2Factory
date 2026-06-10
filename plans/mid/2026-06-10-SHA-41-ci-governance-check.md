---
linear_issue: SHA-41
title: CI never runs scripts/check_governance.ps1 required by AGENTS.md
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add governance acceptance check to CI

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Mid

## Problem

`AGENTS.md` and `governance-acceptance.md` require `scripts/check_governance.ps1`, but GitHub Actions never runs it. Governance line-limit, Hermes marker, and router reference regressions can merge silently.

## Scope

Add CI matrix task running governance acceptance. Use `pwsh` on Linux or Python port if PowerShell unavailable. Failures block merge.

## Non-goals

- Changing governance line limits or router content.
- Fixing currently failing governance violations in this card.
- Folding checks into unrelated lint without explicit signal.

## Implementation Plan

1. Add `governance` to `ci.yml` matrix (or dedicated job).
2. Invoke `pwsh -File scripts/check_governance.ps1` on `ubuntu-latest`; if unavailable, add `python scripts/check_governance.py` port.
3. Document CI invocation in `docs/agent-workflows/governance-acceptance.md` if platform differs.
4. Verify job fails on intentional line-limit violation (local dry-run).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/check_governance.ps1`
- `docs/agent-workflows/governance-acceptance.md`
- `scripts/check_governance.py` (optional port)

## Validation Plan

- build: CI governance job passes on clean branch
- manual verification: introduce >75-line `.mdc` router locally; confirm check fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pre-existing governance violations may block first CI enablement — fix or waive explicitly per issue non-goals.
