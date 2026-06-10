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

# Plan: Optional local pytest drift check and related-gate tracking (SHA-44 Low)

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

Even after the Mid CI gate lands, developers may want faster local feedback than waiting for GitHub Actions. Existing `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` only checks a few lab overlay class substrings in `app.css` — not a full rebuild drift gate. Other frontend bundle drift risks (SHA-35 graph-layout, SHA-40 recipe-graph-editor, SHA-42 locale catalogs) remain separate cards.

## Scope

Optional follow-ups only if the implementer wants local parity with CI:

1. Add a repo-level contract test that shells out to `npm run build:css` and asserts a clean `git diff` on `app.css`.
2. Cross-link the new CI gate in operator docs beside existing frontend build notes.
3. Confirm SHA-35, SHA-40, SHA-42 remain tracked separately (no umbrella job).

## Non-goals

- Do not implement graph-layout, recipe-graph-editor, or locale drift gates in this card.
- Do not replace CI with pytest-only enforcement.
- Do not expand pytest substring checks into full CSS content assertions.

## Implementation Plan

1. Decide whether local pytest feedback is worth the Node dependency in unit tests (skip if CI-only is sufficient).
2. If yes: add `tests/unit/web/test_app_css_drift.py` (or extend an existing web test module) that:
   - Skips when `npm` is unavailable (mark with `pytest.importorskip` or env guard).
   - Runs `npm run build:css` via `subprocess`.
   - Asserts `git diff --exit-code django_apps/web/static/web/css/app.css` returns 0.
3. Add a one-line note in `DESIGN.md` and `structure.md` pointing operators to `npm run build:css` and the CI gate.
4. Verify related issues SHA-35, SHA-40, SHA-42 stay open and unmerged into this workflow.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (reference only)
- `tests/unit/web/test_app_css_drift.py` (optional new)
- `DESIGN.md`
- `structure.md`

## Validation Plan

- lint: `ruff check tests/unit/web/` (if test added)
- typecheck: N/A
- tests: `pytest tests/unit/web/test_app_css_drift.py -v` (if added; requires Node)
- build: `npm run build:css`
- manual verification: Run pytest locally with Node installed; confirm skip behavior without Node

## Acceptance Criteria

- [ ] Matches the source issue spec Low section.
- [ ] Stays within optional/local-feedback scope.
- [ ] SHA-35, SHA-40, SHA-42 are not folded into this work.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pytest subprocess + Node in CI may duplicate the dedicated workflow step; prefer CI as source of truth.
- Substring guards in `test_asteroid_lab_ui_strings.py` remain partial coverage even with this optional test.
