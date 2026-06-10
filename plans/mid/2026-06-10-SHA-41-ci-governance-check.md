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

# Plan: Add governance acceptance check to CI

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Mid

## Problem

`AGENTS.md` § Governance Files requires agent governance files to stay within line limits and points operators to `scripts/check_governance.ps1` as the acceptance check. `docs/agent-workflows/governance-acceptance.md` documents the same script for post-governance-change validation. GitHub Actions never runs this script, so PRs that exceed line caps on `AGENTS.md` or `.cursor/rules/*.mdc`, drop Hermes handoff markers, or break router references can merge while local governance acceptance would fail.

## Scope

Add a CI matrix task (or dedicated job) that runs governance acceptance and blocks merge on failure. On Linux runners (`ubuntu-latest`), either invoke the existing PowerShell script via `pwsh` or add a Python equivalent that mirrors `scripts/check_governance.ps1` checks.

## Non-goals

- Changing governance line limits or router content
- Folding governance checks into unrelated lint rules without an explicit failing signal
- Fixing any currently failing governance violations in this card
- Addressing related CI gaps in SHA-19 (`manage.py check`) or SHA-20 (mypy scope)

## Implementation Plan

1. Inspect `scripts/check_governance.ps1` and enumerate all checks: root/nested `AGENTS.md` line limits, `.cursor/rules/*.mdc` line limits, `root.mdc` Hermes routes, `agent_scope.mdc` handoff exception, `hermes-handoff.md` markers, `AGENTS.md` validation command presence. Note WARN vs FAIL exit semantics (WARN exits 0).
2. Decide CI invocation path for `ubuntu-latest`:
   - **Option A (preferred if zero deps):** Add `scripts/check_governance.py` that ports the PowerShell logic verbatim; keep `.ps1` as the Windows/local canonical entry and have both share behavior.
   - **Option B:** Add a `governance` matrix step using `actions/setup-powershell` or `pwsh` on the runner, then `pwsh -File scripts/check_governance.ps1`.
3. Add `governance` to the `ci.yml` matrix (alongside `lint`, `typecheck`, etc.) or a standalone job with the same `fail-fast: false` strategy pattern.
4. Wire the matrix case:
   ```yaml
   governance) python scripts/check_governance.py ;;  # or pwsh -File scripts/check_governance.ps1
   ```
5. Run the chosen command locally on Linux to confirm current repo state passes (or document known pre-existing failures without fixing them — out of scope).
6. Update `docs/agent-workflows/governance-acceptance.md` with CI invocation (Linux vs Windows) if paths differ.
7. Optionally add a minimal unit test for `check_governance.py` asserting FAIL on a synthetic over-limit fixture (only if test harness is trivial; not required if script is self-contained).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `scripts/check_governance.ps1` (reference only unless deduplicating)
- `scripts/check_governance.py` (new, if Option A)
- `docs/agent-workflows/governance-acceptance.md`
- `AGENTS.md` (reference only)

## Validation Plan

- lint: `ruff check .` (unchanged)
- typecheck: `mypy django_apps config src` if Python port added
- tests: run new governance unit test if added; otherwise manual script invocation
- build: N/A
- manual verification:
  - `python scripts/check_governance.py` (or `pwsh -File scripts/check_governance.ps1`) locally — expect exit 0 on clean tree
  - Push branch and confirm CI `governance` matrix job runs and fails on intentional violation (smoke in PR description if needed)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Pre-existing violations:** If governance check currently fails on `master`, CI will go red immediately. Issue non-goals say do not fix violations here — may need a follow-up card or temporary allowlist (avoid unless explicitly approved).
- **PowerShell on Linux:** `pwsh` is not installed by default on all dev machines; Python port improves Linux/CI parity and local dev on Linux agents.
- **WARN semantics:** Script WARN (root `AGENTS.md` above soft target) must remain exit 0 in CI to match `AGENTS.md` policy.
- **Branch name mismatch:** `ci.yml` triggers on `main` push; repo default branch may be `master` — unrelated to this card but affects when CI runs on push.
