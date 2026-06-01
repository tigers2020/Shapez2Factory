# Manual: Cursor Usage Habits · Context · Agent-Native Engineering

This document is **on-demand reference** placed in `documents/ai/manuals/` **to avoid growing the rules the agent reads every turn**. The canonical always-on rules are [`AGENTS.md`](../../../AGENTS.md) and [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc).

Root [`AGENTS.md`](../../../AGENTS.md) defines **Spec-first SDD · Small PR · Test-gated · Review-driven** workflow; this manual is on-demand detail.

## 1. Why Do Token Limits Deplete Quickly?

- Each send in chat/composer **bundles conversation history, attachments, some system content, and rules into input context**. The longer the thread, the **larger the input** for the same question.
- When logs, errors, or code chunks from unrelated work stay in one thread, **noise and cost rise together**. When quality drops, fix cycles can increase **output tokens** too.

Concrete **plan limits, per-model pricing, and multipliers** change over time — check Cursor app **Settings · Billing / Usage** and official documentation.

## 2. Harness Perspective (Human ↔ Agent ↔ Harness)

The agent operates through prompts, rules, code search, terminal, and model. Harness = [`.cursor/rules/workflow.mdc`](../../../.cursor/rules/workflow.mdc) + [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) + [`AGENTS.md`](../../../AGENTS.md) + [`protocols/README.md`](../../../protocols/README.md) + [`.cursor/skills/`](../../../.cursor/skills/) (e.g. `quality-check`, `cli-boundary`, `write-tests`).

## 3. Intent Precision and Prompts

- **Bad example**: "Fix this" with no spec, scope, or acceptance.
- **Good example**: Link CANON spec or [`contract-brief.md`](../templates/contract-brief.md); declare **Position · Authority · Acceptance**; list paths/symbols; prohibitions; `pytest` path; PR purpose (e.g. "PR-3: spec + acceptance tests only — no production edits").

Higher intent precision reduces hallucination and unrelated exploration, making architectural consistency easier to maintain.

## 4. Using Context as Working Memory

- For large features or hard bugs, **start a new thread** is recommended.
- When behavior gets weird, **resetting the session** may be better.
- Large repos can spike tokens and lower reasoning quality, so keep **reference scope minimal** (`@` files/folders only as needed).

## 5. Code Search Strategy

| Type | Means | Use |
|------|------|------|
| **Literal** | `grep`/ripgrep, symbol search | Exact function names, strings, error messages |
| **Semantic** | Queries like "where is auth?", semantic search, Serena, etc. | Flow, middleware, indirect calls |

Use both together and **understand first**, then narrow the change scope.

## 6. Subagents and Task Isolation

Run broad exploration and impact analysis in **separate context** (subagents, background tasks, etc.) and bring **results only** back to the main thread to reduce main-context contamination. Separate work with different topics like Pass, Recovery, Replay, and verification.

## 7. Do Not Edit Before Understanding

Agents may duplicate utilities they don't know about, ignore layers/patterns, or cause **architecture drift**.

Solver, replay, CLI, and layer placement are intertwined — confirm call relationships and **CANON spec** before edits. Workflow (SDD): **spec/contract brief → acceptance tests from spec → small PR** ([`AGENTS.md`](../../../AGENTS.md), [`workflow.mdc`](../../../.cursor/rules/workflow.mdc)).

## 8. Feature Development Flow (Canonical)

1. **Problem + contract brief** ([`templates/contract-brief.md`](../templates/contract-brief.md) or CANON spec)
1b. **Adversarial plan review (optional)** — [`grill-me-shapez2`](../../../.cursor/skills/grill-me-shapez2/SKILL.md) when algorithm/DTO/Layer scope branches; read-only; before contract amendment
2. **PR plan** — one purpose ([`templates/pr-plan.md`](../templates/pr-plan.md))
3. Human scope approval (non-trivial contract changes)
4. Audit (read-only) if behavior uncertain
5. **Acceptance tests from spec** when behavior changes
6. Minimal implementation for **this PR only**
7. Verification — narrow `pytest` → `ruff`; PR full gate per [`testing.md`](testing.md). **No `-q` / `--quiet` / `--tb=no`**
8. Review → merge → doc sync if public contract changed

Split large work into PR-1 audit · PR-2 contract/spec · PR-3 acceptance tests · PR-4 implement · PR-5 cleanup.

## 9. Debugging Principles

1. Must be **reproducible**.
2. **Minimize** to smallest case.
3. **Isolate** change scope.
4. Form **root-cause hypothesis**, then verify with evidence.
5. Add **logs/instrumentation** when needed.
6. Leave **regression tests**.

A one-line "fix this error" is less efficient than providing runtime evidence, hypothesis, and reproduction together.

## 10. Multi-Model and Cross-Validation

Running the same bug through **different models/agents** in parallel can yield different approaches. But **explanation is not proof**: root cause, edge cases, type safety, etc. must be **verified by humans, tests, and logs**.

## 11. Code Review and Commits

- AI-written code gets the **same human review standards**.
- Large diffs split into **semantic commits** improve reviewer comprehension.

## 12. Test and CI Cost

In the agent era, tests, lint, and type-check run **often in short cycles**, so **slow suites and excessive full pytest** increase cost and wait time. **Default: run only test files/directories corresponding to code changed this turn**, narrowed by markers/paths ([`testing.md`](testing.md) top, [`AGENTS.md`](../../../AGENTS.md) test table). Full `python -m pytest` from root **only when necessary**. Output suppression (`-q`, `--quiet`, `--tb=no`) is **forbidden** — [`testing.md` § pytest output rules](testing.md).

For regression prevention, leave **tests whenever possible** for each feature/bug fix.

## 13. Rules vs Skills

| Distinction | Role | This repo examples |
|------|------|------------|
| **Rules** | Always-on short directives | `shapez2-core.mdc` + `AGENTS.md` (glob rules only on working paths) |
| **Skills** | Procedure bundles opened only when needed | `grill-me-shapez2`, `quality-check`, `write-tests`, `cli-boundary`, `shapez2-workflow`; reference this manual via `@` |

Do not duplicate long bodies in rule files; put them in manuals/plans and link.

## 14. Relationship to This Repo (Practical Habits Table)

| Habit | Description |
|------|------|
| Separate threads by work unit | When a task ends or topic changes, **start a new chat**. (Same goal as `/clear` — "clear the room".) |
| Model selection | Default to relatively lighter models; switch to heavier only for **design · hard debugging** when needed. |
| Minimize reference scope | `@file` · `@folder` only for **paths truly needed**. Broad folder/whole-codebase exploration requests inflate context via tool calls/search results. |
| Concretize prompts | Write file paths, symbol names, completion criteria (test commands, etc.) to reduce **unnecessary exploration**. |

- Only [`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) and [`AGENTS.md`](../../../AGENTS.md) ride **every turn**. Don't duplicate same content in rules; put in **manuals · plans** and open via `@`.
- MCP is on-demand. Disable unused MCP servers to reduce load (Cursor slim guide: [`cursor_slim_setup.md`](cursor_slim_setup.md)).
- Structure/symbol tracing: **Serena** + `@mcp` (read `initial_instructions` first).

## 15. Transcript Philosophy and Project Alignment (Summary)

| Idea | Mapping in this repo |
|----------|-------------------|
| Spec-first | CANON spec · [`contract-brief.md`](../templates/contract-brief.md) · [`pr-plan.md`](../templates/pr-plan.md) |
| Small PR | One contract change or one refactor purpose per PR |
| Test-gated | Acceptance tests from spec before production (contract/regression) |
| Position not persona | Task prompt: scope · authority · acceptance · stop conditions |
| Context separation | New thread per PR purpose · subagents for broad audit |
| Verification gates | [`testing.md`](testing.md) dual gate |
| Authority | Superseded docs ≠ implementation context ([`START_HERE.md`](../START_HERE.md)) |

## 16. Related Manuals

- Large-scope changes: plans · checklist in [`documents/ai/`](../../README.md)
- Test sections: [`testing.md`](testing.md)

## Cloud VM

Applies to Cursor Cloud / remote VM only.

- **Service**: Django dev server only. No Docker, Redis, Celery, or external DB required.
- **DB**: SQLite by default. First run `python3 manage.py migrate` to create `db.sqlite3` (idempotent).
- **Server**: `python3 manage.py runserver 0.0.0.0:8000` (`python` may not be on PATH).
- **PATH**: `export PATH="/home/ubuntu/.local/bin:$PATH"` (`black`, `ruff`, `mypy`, `pytest`).
- **Solver API** (`POST /api/solver/solve/`): CSRF — get `csrftoken` cookie from page, then send `X-CSRFToken` + cookie.
- **Frontend**: CSS/JS bundles committed. Run `npm install` / `npm run build` only when editing `assets/css/` or `frontend/`.
- **Graph preview**: default `playwright_png`. Without Playwright, set `SOLVER_GRAPH_PREVIEW_RENDERER=noop` in `.env.debug` (see `.env.debug.example`, [`environment.md`](environment.md)).
- **Verification commands**: [`testing.md`](testing.md) table. `black --check .` may have 1 existing format issue in `django_apps/web/views/macro_staff.py`.

## 17. Caveman Communication (Required)

**Purpose**: Reduce **output tokens** in chat and closing reports (practical 15–40% target; no exaggeration). **Keep internal reasoning · gate quality**; compress narration only.

### Two layers (do not conflate)

| Layer | When | Canon |
|------|------|------|
| **Chat style** | Every user-facing turn | [`AGENTS.md` Communication](../../../AGENTS.md) · [shapez2-core.mdc Caveman chat](../../../.cursor/rules/shapez2-core.mdc) — Korean, terse, high-signal |
| **Six-section close** | End of implementation / review turns | Headings below; same titles in shapez2-core |

**Off switch:** `stop caveman` or `normal mode`. **Auto-clarity:** security warnings, irreversible actions, multi-step instructions where fragments mislead — then resume caveman.

**Global skill:** when user attaches `/caveman` or `.agents/skills/caveman/SKILL.md`, follow it for phrasing; **do not** replace six-section titles.

### 3 Layers (cross-reference)

| Layer | Canon |
|------|------|
| Routing | [`AGENTS.md`](../../../AGENTS.md) |
| Rule (alwaysApply) | [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) · glob [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) |
| Manual | this section · [`testing.md`](testing.md) · [`checklist.md`](../checklist.md) |

For repo work, prioritize **AGENTS + shapez2-core** over long prose.

### MUST — 6 sections (order · titles must not change)

```text
## Summary
## Files
## Contracts
## Tests
## Risks
## Next
```

| Section | Content |
|----|------|
| Summary | 1–3 bullets; state classification + PR purpose |
| Files | `path — why` |
| Contracts | invariants · DTO · schema |
| Tests | `cmd — pass\|fail\|skipped — note` |
| Risks | regression · `uncertain:` · `assumption:` |
| Next | what follows; use 「complete」 only when finished |

**Closing without 6 sections = incomplete** ([`workflow.mdc`](../../../.cursor/rules/workflow.mdc) checklists).

### Exceptions (6-section omission)

1. Plan mode plan body (chat after implementation still uses 6 sections)
2. User explicitly requests 「detailed explanation · education · review」
3. Writing/editing **`documents/` file bodies** (canonical project language)

### On-demand

Long replay/DTO sessions: optional link hub [`.cursor/skills/_archive/caveman-mode/SKILL.md`](../../../.cursor/skills/_archive/caveman-mode/SKILL.md) (`@caveman-mode`) — checklist only; chat + close canon stays AGENTS + shapez2-core.
