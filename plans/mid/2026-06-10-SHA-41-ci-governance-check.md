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

# Plan: Run governance acceptance check in CI

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Mid

## Problem

`AGENTS.md` and `docs/agent-workflows/governance-acceptance.md` require `scripts/check_governance.ps1` as the acceptance check for agent governance file line limits, Hermes handoff markers, and router references. GitHub Actions never runs this script, so governance regressions can merge while local acceptance would fail.

## Scope

Add a CI matrix task (or pre-merge step) that runs governance acceptance. On Linux runners, use `pwsh` for the existing script or add a small Python equivalent invoked from `ci.yml`. Ensure failures block merge.

## Non-goals

- Changing governance line limits or router content.
- Folding governance checks into unrelated lint rules without an explicit failing signal.
- Fixing any currently failing governance violations in this card.

## Implementation Plan

1. Inspect `scripts/check_governance.ps1` for platform dependencies (PowerShell-only vs portable logic).
2. Add `governance` task to `.github/workflows/ci.yml` matrix.
3. Prefer `pwsh -File scripts/check_governance.ps1` on `ubuntu-latest` (install PowerShell if not present via `actions/setup-dotnet` or use preinstalled `pwsh`).
4. If PowerShell is unreliable on CI, port checks to `python scripts/check_governance.py` mirroring script behavior and call from CI.
5. Document CI invocation in `docs/agent-workflows/governance-acceptance.md` if platform-specific.
6. Verify job fails on intentional governance violation (e.g., temp oversized `.mdc` in test branch) before merge.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/check_governance.ps1` (read; optional Python port)
- `docs/agent-workflows/governance-acceptance.md`
- `AGENTS.md` (reference only; no content change unless doc cross-link needed)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: CI governance job pass on clean main
- build: N/A
- manual verification: `pwsh -File scripts/check_governance.ps1` locally; CI job mirrors result

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pre-existing governance violations may cause immediate CI red when gate is added; scope says do not fix violations in this card — may need follow-up cleanup PR or WARN-only first run (document if blocked).
- Related SHA-19 (`manage.py check`) and SHA-20 (mypy scope) remain separate CI gaps.
