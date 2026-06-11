# AGENTS.md

## Mission
shapez2 Factory Planner governance: short rules, strict contracts, small safe changes, fast verification, no stale-doc authority.

## Default Workflow
1. Use `/using-superpowers` first: check relevant skills before analysis, planning, or edits.
2. Use `/caveman` always: Korean, direct, compressed, blunt, no fluff, no cheerleading, no vague agreement.
3. Read order when needed: `AGENTS.md` -> `structure.md` -> `documents/ai/START_HERE.md` -> current canon/spec -> code/tests. **When `graphify-out/graph.json` exists**, run `/graphify` query/path/explain before wide repo search or multi-module reads (`.cursor/rules/graphify.mdc`).
4. Plan before implementation. No production code change until intended contract is clear.
5. Clean git surface before edits: no dirty branch/worktree unless user scoped those files (`.cursor/rules/git-worktree.mdc`).
6. Prefer one PR-sized purpose. Split mixed contract/refactor/UI/runtime work.
7. Do not commit, push, open PRs, or mark external work closed unless user asks.

## Agent Scope

Closed-world execution only — tasks explicitly listed in the approved plan or user prompt. Handoff prep excepted: `.cursor/rules/agent_scope.mdc`. Stop marker: `STOPPED_AT_APPROVED_SCOPE`. Anti-silent-failure: after every run, verify actual artifact output (exit code + diff) — "forward-looking green" without real verification counts as red.

## Cursor ↔ Hermes Skill Suggestion

Cursor implements; Hermes researches and suggests skills — not APPROVE/BLOCK. Canon: `docs/agent-workflows/hermes-skill-suggestion.md`, `skill-trust-boundary.md`, `hermes-handoff.md`. Routers: `00-hermes-skill-suggestion.mdc`, `01-hermes-handoff-format.mdc`.

## Tool Routing

- **Graphify (mandatory when graph exists):** architecture, coupling, boundaries, cross-module paths, unfamiliar subsystems — `/graphify` on `graphify-out/graph.json` before wide grep (`graphify.mdc`, `docs/agent-workflows/graphify-routine.md`). Human viz: `graphify-out/graph.html`, Obsidian `graphify-out/obsidian/` (not repo root). After code-only edits: `graphify update django_apps` / `src`. Separate EXTRACTED vs INFERRED edges.
- Playwright: when browsing, browser testing, UI flow checks, screenshots, or rendered-page verification matter, use `/playwright` and `.cursor/rules/playwright.mdc`. Prefer real browser evidence; store artifacts under `output/playwright/`.

## Shapez2 Routing

Use `/grill-me-shapez2` for Shapez2/Asteroid Lab/solver work when contract is ambiguous. Pipeline: `shapez2-domain.mdc` -> `docs/agent-workflows/hermes-skill-suggestion.md`. Canon/spec/ADR beats stale docs and agent memory.

## SDD / Testing (ICE: Intent · Context · Expectations)

- ICE first — Intent(무엇), Context(제약), Expectations(언제 끝). Spec 전체가 아니라 3층 분할로 acceptance judgment 인간 유지.
- Tests verify contracts, not agent guesses.
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

**AGENTS.md size:** root target ~75 lines; review/split before 120. Nested/module `AGENTS.md` may reach ~150 for local commands, safety, tests, contracts; split past 150. Do not paste long specs — link focused docs and say when to read them.

Line-count WARN is non-blocking. Do not edit `AGENTS.md` or rules solely to clear a WARN. Fix only hard failures: root `AGENTS.md` >120 lines, nested `AGENTS.md` >150 lines, or `.cursor/rules/*.mdc` >75 lines. Preserve behavior-changing rules over formatting, examples, or explanations.

`.cursor/rules/**/*.mdc`: thin routers, stay <= 75; operational detail in `docs/agent-workflows/`. Check: `scripts/check_governance.ps1`.

## Conflict Precedence

1. User explicit current instruction
2. `AGENTS.md`
3. Matching `.cursor/rules/*.mdc`
4. Current docs/specs/ADRs
5. Agent assumptions

When blocked, say `BLOCKED:` with context, risk, fixes tried, and next step.
