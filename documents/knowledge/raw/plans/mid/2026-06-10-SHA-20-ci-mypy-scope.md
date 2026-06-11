---
linear_issue: SHA-20
title: CI mypy job checks src only; AGENTS.md requires django_apps and config
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Align CI mypy scope with AGENTS.md canon

## Source Issue

- Linear: SHA-20
- Status at planning time: Todo
- Priority: Mid

## Problem

CI runs `mypy src` only; `AGENTS.md` requires `mypy django_apps config src`.

## Scope

Expand CI typecheck to full scope OR document phased rollout if 900+ errors block expansion.

## Non-goals

- Do not mass-fix unrelated type errors outside minimal CI unblock.

## Implementation Plan

1. Run `mypy django_apps config src` locally; count errors.
2. If errors manageable: update `ci.yml` typecheck command to full scope; fix blocking errors in changed modules only if needed for green CI.
3. If errors too many: update `AGENTS.md` and `validation-routine.md` with phased CI scope + tracking issue reference (document decision in PR).
4. Verify `pyproject.toml` mypy config covers all packages.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `AGENTS.md`
- `pyproject.toml`
- `django_apps/`, `config/`, `src/`

## Validation Plan

- typecheck: `mypy django_apps config src`
- CI workflow green on PR

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Large error count may force docs-only interim fix per issue Proposed Approach.
