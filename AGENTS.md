# AGENTS.md

**shapez2 Factory Planner** — agent entry. Project rules: [`.cursor/rules/`](.cursor/rules/) · manuals: [`documents/ai/`](documents/ai/).

## Workflow

Spec-first → contract brief → failing tests (behavior change) → minimal change → gate. **One PR · one purpose.** Brief before production when behavior changes.

[`contract-brief.md`](documents/ai/templates/contract-brief.md) · [`workflow.mdc`](.cursor/rules/workflow.mdc)

## Communication

Chat: **Korean** + **caveman** (`stop caveman` / `normal mode` off). Docs/code/commits/PRs: **English**. Close: six sections in [`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc).

## Agent scope

Per task: **Position · Mission · Authority · Acceptance · Stop**. Human: contract & merge. Agent: scoped work within authority. **No** commit/push/PR/merge unless user asks. Unclear → ask; mark `uncertain:` in Risks.

## Read order

`structure.md` (path SoT) → [`START_HERE.md`](documents/ai/START_HERE.md) → task CANON spec → [`manuals/`](documents/ai/manuals/) for work type → relevant source/tests only.

CANON spec/ADR = design authority. ACTIVE plan = tracker only. Superseded/deleted ≠ implementation context.

## Gates

| When | Commands |
|---|---|
| Iteration | `python -m pytest <path>` · `ruff check <paths>` — no `-q`/`--quiet`/`--tb=no` |
| PR | `scripts/test_full.ps1` · `ruff check .` · `mypy django_apps config src` · `black --check .` |
| Daily | `scripts/test_fast.ps1` |

Details: [`testing.md`](documents/ai/manuals/testing.md). Regression: test fails **before** fix.

## Status

**DONE** — one PR purpose · brief met · tests if behavior changed · gates evidenced.

**BLOCKED** — missing context · scope overflow · no CANON for contract change.

Forbidden shortcuts · layers · work classification: [`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc).
