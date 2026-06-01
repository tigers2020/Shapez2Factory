# AGENTS.md

## Mission

shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## Default Workflow

1. Use `/using-superpowers` first: check relevant skills before analysis, planning, or edits.
2. Use `/caveman` always: Korean, direct, compressed, blunt, no fluff, no cheerleading, no vague agreement.
3. Read order when needed: `AGENTS.md` -> `structure.md` -> `documents/ai/START_HERE.md` -> current canon/spec -> code/tests.
4. Plan before implementation. No production code change until intended contract is clear.
5. Prefer one PR-sized purpose. Split mixed contract/refactor/UI/runtime work.
6. Do not commit, push, open PRs, or mark external work closed unless user asks.

## Shapez2 Routing

Use `/grill-me-shapez2` when the user/task/chat touches Shapez2, Asteroid Lab, solver layers, asteroid mining, placement, routing, replay, UI, reconstruction, transport, belt/pipe, L2/L3/L4, rim greedy placement, or related project code.

For Shapez2/Asteroid Lab, current canon/spec/ADR beats stale older docs, archived notes, and agent memory.

## SDD / Testing

- Spec/contract first; tests verify contracts, not agent guesses.
- Acceptance tests must map to real behavior: Given/When/Then, regression, golden, invariant, schema, or API contract.
- Do not add weak tests that merely pass or assert implementation trivia.
- Do not weaken, delete, skip, or relax tests to force green.
- Regression work needs a failing repro before the fix unless impossible; record why if skipped.
- Solver/replay/runtime changes must preserve invariants named in matching rules and canon docs.

## Validation

Use focused gates while iterating, then broader gates before done claims:

```bash
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

PR/full gate when requested: `scripts/test_full.ps1` plus lint/type/format. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Scope / Permissions

- Allowed edits by default: source, tests, docs, governance files.
- This governance task scope: only `AGENTS.md` and `.cursor/rules/**/*.mdc`.
- Ask before editing `.env`, secrets, CI/deploy, security-sensitive config, or doing large delete/rename.
- Do not invent commands, tool behavior, MCP behavior, or unverified pass claims.

## Governance Files

`AGENTS.md` and every `.cursor/rules/**/*.mdc` must stay <= 75 lines.

Canonical project rules live here. Cursor `.mdc` files are thin routers: frontmatter, trigger, globs, and pointers only.

## Conflict Precedence

1. User explicit current instruction
2. `AGENTS.md`
3. Matching `.cursor/rules/*.mdc`
4. Current docs/specs/ADRs
5. Agent assumptions

When blocked, say `BLOCKED:` with context, risk, fixes tried, and next step.
