---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document build:css CI gate and optional local drift contract test

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

Operators and contributors lack fast local feedback for `app.css` drift beyond CI. Existing `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` only checks a few lab overlay class substrings — not a full rebuild gate. Workflow docs (`DESIGN.md`, `structure.md`) do not yet mention the planned CI enforcement.

## Scope

- Document the new `build-css-check` CI gate beside existing frontend build notes in `DESIGN.md` and `structure.md`.
- Optionally add a repo-level contract test that shells out to `npm run build:css` and asserts a clean diff for local fast feedback.

## Non-goals

- Do not replace the CI gate (covered by Mid plan `plans/mid/2026-06-10-SHA-44-ci-build-css-drift-gate.md`).
- Do not add substring-only guards as a substitute for rebuild verification.
- Do not document or implement SHA-35/SHA-40/SHA-42 bundle gates here.

## Implementation Plan

1. After the Mid-plan CI gate lands, add a short subsection under `DESIGN.md` § Tailwind CSS noting that CI runs `npm run build:css` + `git diff --exit-code` on `django_apps/web/static/web/css/app.css`.
2. Update `structure.md` build table with the new CI task name and local reproduction command (`npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`).
3. Evaluate whether `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` should gain a `@pytest.mark.slow` contract test that runs the same shell sequence; skip if CI-only enforcement is sufficient and Node is not available in fast test environments.
4. If adding the contract test, gate it behind a marker (`slow` or `frontend`) so `test-fast` remains unaffected.

## Files / Areas Likely Affected

- `DESIGN.md`
- `structure.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)
- `pytest.ini` or `pyproject.toml` markers (only if new marker needed)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `powershell -File scripts/test_fast.ps1`
- build: N/A
- manual verification: Confirm docs reference the CI gate and local repro command

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Relevant docs mention the new gate.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Local contract test requires Node/npm in dev environments; may be undesirable for Python-only contributors — defer if CI gate alone is enough.
- Pytest substring guards for lab classes remain partial coverage; document that limitation explicitly.
