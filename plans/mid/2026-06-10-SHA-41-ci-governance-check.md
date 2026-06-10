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

# Plan: CI never runs scripts/check_governance.ps1 required by AGENTS.md governance acceptance

## Source Issue

- Linear: SHA-41
- Status at planning time: In Progress
- Priority: Mid

## Problem

`AGENTS.md` § Governance Files requires agent governance files to stay within line limits and points operators to `scripts/check_governance.ps1` as the acceptance check. `docs/agent-workflows/governance-acceptance.md` documents the same script. GitHub Actions never runs this script, so PRs that exceed line caps on `AGENTS.md` or `.cursor/rules/*.mdc`, drop Hermes handoff markers, or break router references can merge while local governance acceptance would fail.

## Scope

Add a CI matrix task (or dedicated job) that runs governance acceptance. On Linux runners, use `pwsh -File scripts/check_governance.ps1` if PowerShell is available on `ubuntu-latest`, or add a small Python equivalent invoked from `ci.yml`. Ensure failures block merge.

## Non-goals

- Changing governance line limits or router content
- Folding governance checks into unrelated lint rules without an explicit failing signal
- Fixing any currently failing governance violations in this card

## Implementation Plan

1. Read `.github/workflows/ci.yml` matrix structure (current tasks: `lint`, `typecheck`, `format`, `test-fast`, `test-integration`).
2. Verify `pwsh` availability on `ubuntu-latest` (GitHub-hosted runners include PowerShell Core). If available, add `governance` matrix task running `pwsh -File scripts/check_governance.ps1`.
3. If `pwsh` is unavailable or flaky, port `scripts/check_governance.ps1` checks to `scripts/check_governance.py` and invoke `python scripts/check_governance.py` from CI.
4. Document the CI invocation in `docs/agent-workflows/governance-acceptance.md` if platform differs from local `powershell -File` usage.
5. Confirm the new job fails when governance checks fail (do not fix pre-existing violations in this card).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/check_governance.ps1` (reference only unless Python port added)
- `scripts/check_governance.py` (if Python port required)
- `docs/agent-workflows/governance-acceptance.md`
- `AGENTS.md` (reference)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: CI workflow syntax valid
- manual verification: `pwsh -File scripts/check_governance.ps1` locally; confirm CI matrix runs governance task on PR

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pre-existing governance violations may cause first CI run to fail — out of scope for this card per issue non-goals.
- Python port must mirror PowerShell semantics (WARN exit 0, FAIL exit 1) if `pwsh` path is skipped.
