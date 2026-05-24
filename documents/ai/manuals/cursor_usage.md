# Manual: Cursor Usage Habits · Context · Agent-Native Engineering

This document is **on-demand reference** placed in `documents/ai/manuals/` **to avoid growing the rules the agent reads every turn**. The canonical always-on rules are [`AGENTS.md`](../../../AGENTS.md) and [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc).

The **Agent-Native Engineering (Summary)** section in root [`AGENTS.md`](../../../AGENTS.md) and the body below share the same philosophy.

## 1. Why Do Token Limits Deplete Quickly?

- Each send in chat/composer **bundles conversation history, attachments, some system content, and rules into input context**. The longer the thread, the **larger the input** for the same question.
- When logs, errors, or code chunks from unrelated work stay in one thread, **noise and cost rise together**. When quality drops, fix cycles can increase **output tokens** too.

Concrete **plan limits, per-model pricing, and multipliers** change over time — check Cursor app **Settings · Billing / Usage** and official documentation.

## 2. Harness Perspective (Human ↔ Agent ↔ Harness)

The agent operates through a combination of prompts, rules, code search, terminal, and model. In this repo, [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc), [`AGENTS.md`](../../../AGENTS.md), [`protocols/README.md`](../../../protocols/README.md), and skills ([`.cursor/skills/shapez2-harness/SKILL.md`](../../../.cursor/skills/shapez2-harness/SKILL.md), [`.cursor/skills/cursor-shapez2-harness/SKILL.md`](../../../.cursor/skills/cursor-shapez2-harness/SKILL.md)) comprise the **harness**.

## 3. Intent Precision and Prompts

- **Bad example**: A one-line request that invites broad exploration and speculative implementation.
- **Good example**: Specify paths/symbols pointing to existing patterns, logs or reproduction steps, desired structure, prohibitions (e.g. no solver behavior changes, no underscore toggle renames like `func`↔`_func`), and completion criteria (e.g. `pytest` path to run).

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

In this repo's mining/placement solver, replay, recovery, routing, protected corridor, reclaim, Pass, etc. are **intertwined**, so changes without confirming call relationships and `documents/` canon are risky. Project rule: meaningful changes follow **research · plan · approval gates** ([`AGENTS.md`](../../../AGENTS.md), [`protocols/README.md`](../../../protocols/README.md)).

## 8. Feature Development Flow (Recommended)

1. Planning (clarify questions · scope)
2. Clarifying questions
3. Execution plan broken into **self-verifiable steps**
4. Implementation
5. Verification — **Contract-first TDD** ([`testing.md`](testing.md)): iterative narrow `pytest` → PR full gate (`ruff` → `black --check` → `mypy` → full `pytest`). **No `-q` / `--quiet` / `--tb=no`** (hides failure detail).
6. Iterate

Don't implement big features in one shot; set pass criteria at each step for safety.

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
| **Skills** | Procedure bundles opened only when needed | `/merge-all`, `shapez2-harness`, `cursor-shapez2-harness`, `data-pipeline-harness`, `code-review-harness`, `research-harness` skills, reference this manual via `@` |

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
| Plan-first | `documents/` plans · approval, [`checklist.md`](../checklist.md) |
| Context separation | threads · subagents · phase documents |
| Instrumentation · replay | computation_cycle, events · recovery traces, etc. (follow module canon) |
| Verification gates | [`testing.md`](testing.md) dual gate: iterative narrow `pytest` / PR `ruff`→`black --check`→`mypy`→`pytest` |
| Abstraction boundaries | recovery · replay · routing · corridor etc. **watch for duplicate abstractions** ([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) simplicity) |

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

## 17. Caveman Output (Required)

**Purpose**: Reduce **output tokens** in chat/closing reports (practical 15–40% target; no exaggeration). **Keep internal reasoning · gate quality**, compress narration only.

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
| Summary | 1–3 bullets; for 3-step implementation use `[Simon]` · `[owner]` bullets before code |
| Files | `path — why` |
| Contracts | invariants · DTO · schema |
| Tests | `cmd — pass\|fail\|skipped — note` |
| Risks | regression · `uncertain:` · `assumption:` |
| Next | what follows; use 「complete」 only when finished |

**Closing without 6 sections = incomplete** ([`checklist.md`](../checklist.md)).

### Exceptions (6-section omission)

1. Plan mode plan body (chat after implementation still uses 6 sections)
2. User explicitly requests 「detailed explanation · education · review」
3. Writing/editing **`documents/` file bodies** (canonical project language)

### On-demand

Long replay/DTO sessions: [`.cursor/skills/caveman-mode/SKILL.md`](../../../.cursor/skills/caveman-mode/SKILL.md) (`@caveman-mode`).
