# AGENTS.md

## Mission

shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## Default Workflow

1. Use `/using-superpowers` first: check relevant skills before analysis, planning, or edits.
2. Use `/caveman` always: Korean, direct, compressed, blunt, no fluff, no cheerleading, no vague agreement.
3. Read order when needed: `AGENTS.md` -> `structure.md` -> `documents/ai/START_HERE.md` -> current canon/spec -> code/tests. If `graphify-out/graph.json` exists, query it before broad exploration (see Graphify).
4. Plan before implementation. No production code change until intended contract is clear.
5. Prefer one PR-sized purpose. Split mixed contract/refactor/UI/runtime work.
6. Do not commit, push, open PRs, or mark external work closed unless user asks.

## Agent Scope

Closed-world execution only — tasks explicitly listed in the approved plan or user prompt. Handoff prep excepted: `.cursor/rules/agent_scope.mdc`. Stop marker: `STOPPED_AT_APPROVED_SCOPE`.

## Cursor ↔ Hermes Skill Suggestion

Cursor implements; Hermes researches and suggests skills — not APPROVE/BLOCK. Canon: `docs/agent-workflows/hermes-skill-suggestion.md`, `skill-trust-boundary.md`, `hermes-handoff.md`. Routers: `00-hermes-skill-suggestion.mdc`, `01-hermes-handoff-format.mdc`.

## Graphify

When architecture, coupling, cross-module paths, or unfamiliar subsystems matter: use `graphify-out/graph.json` via `.cursor/rules/graphify.mdc` and `docs/agent-workflows/graphify-routine.md` (`graphify query|path|explain`, or `/graphify <path>` to rebuild). After code-only edits in session: `graphify update <scope>`. Separate AST edges from INFERRED edges before refactor claims.

## Shapez2 Routing

Use `/grill-me-shapez2` for Shapez2/Asteroid Lab/solver work when contract is ambiguous. Pipeline: `shapez2-domain.mdc` -> `docs/agent-workflows/hermes-skill-suggestion.md`. Canon/spec/ADR beats stale docs and agent memory.

## SDD / Testing

- Spec/contract first; tests verify contracts, not agent guesses.
- Acceptance tests: Given/When/Then, regression, golden, invariant, schema, or API contract.
- No weak tests, no relaxed/skipped tests to force green.
- Regression: failing repro before fix unless impossible.
- Solver/replay/runtime: preserve invariants in matching rules and canon docs.

## Validation

Canonical commands — handoff docs and Hermes checklists must reference this section only:

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

When to run which gate: `docs/agent-workflows/validation-routine.md`. PR/full: `scripts/test_full.ps1` plus lint/type/format. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Scope / Permissions

- Allowed edits by default: source, tests, docs, governance files.
- Ask before `.env`, secrets, CI/deploy, security-sensitive config, or large delete/rename.
- Do not invent commands, tool behavior, MCP behavior, or unverified pass claims.

## Governance Files

`AGENTS.md` and every `.cursor/rules/**/*.mdc` must stay <= 75 lines. `.mdc` files are thin routers; operational detail lives in `docs/agent-workflows/`. Check: `scripts/check_governance.ps1`.

## Conflict Precedence

1. User explicit current instruction
2. `AGENTS.md`
3. Matching `.cursor/rules/*.mdc`
4. Current docs/specs/ADRs
5. Agent assumptions

When blocked, say `BLOCKED:` with context, risk, fixes tried, and next step.
