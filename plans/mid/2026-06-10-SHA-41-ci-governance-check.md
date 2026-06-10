---
linear_issue: SHA-41
title: CI never runs scripts/check_governance.ps1 required by AGENTS.md governance acceptance
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CI governance acceptance check

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Mid

## Problem

`AGENTS.md` § Governance Files requires agent governance files to stay within line limits and points operators to `scripts/check_governance.ps1` as the acceptance check. `docs/agent-workflows/governance-acceptance.md` documents the same script for post-governance-change validation. GitHub Actions never runs this script, so PRs that exceed the 75-line cap on `AGENTS.md` or `.cursor/rules/*.mdc`, drop Hermes handoff markers, or break router references can merge while local governance acceptance would fail.

## Scope

Add a CI matrix task (or pre-merge step) that runs governance acceptance. On Linux runners, either install PowerShell for the existing script or add a small Python equivalent invoked from `ci.yml`. Ensure failures block merge.

## Non-goals

- Changing governance line limits or router content.
- Folding governance checks into unrelated lint rules without an explicit failing signal.
- Fixing any currently failing governance violations in this card.

## Implementation Plan

1. Add `governance` to the `.github/workflows/ci.yml` matrix (or dedicated job after checkout).
2. Prefer `pwsh -File scripts/check_governance.ps1` if PowerShell is available on `ubuntu-latest`; verify script enforces line limits, Hermes routes, handoff markers, validation command presence per `scripts/check_governance.ps1`.
3. If PowerShell unavailable or flaky on Linux, port checks to `python scripts/check_governance.py` helper and invoke from CI — keep parity with PS1 checks.
4. Document CI step in `docs/agent-workflows/governance-acceptance.md` if invocation differs by platform.
5. Confirm job fails on intentional violation (e.g. temp oversize `.mdc` in test branch) before merge.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/check_governance.ps1`
- TBD — `scripts/check_governance.py` (if Linux port needed)
- `docs/agent-workflows/governance-acceptance.md`
- `AGENTS.md` (reference only — lines 68–69)

## Validation Plan

- lint: N/A unless Python port added (`ruff check scripts/`)
- typecheck: N/A unless Python port added
- tests: run `pwsh -File scripts/check_governance.ps1` locally on current branch; document exit code
- build: N/A
- manual verification: CI governance job appears in PR checks and blocks on violation

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pre-existing governance violations on `master` may block all PRs once gate lands — track cleanup in Low plan.
- Related SHA-19 (`manage.py check`) and SHA-20 (mypy scope) remain separate CI gaps.
