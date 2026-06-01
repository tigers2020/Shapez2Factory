# AGENTS.md

## Mission

Repo = **shapez2 Factory Planner**. Always: **small safe changes + fast verification + doc sync**.

## Communication language

| Surface | Language |
|---|---|
| Chat with user (questions, plans, reviews, closing summaries) | **Korean** (한국어) |
| Repo docs (`docs/`, `documents/`, ADRs, runbooks, specs, plans) | **English** |
| Code (identifiers, comments, docstrings), commit messages, PR title/body | **English** |

Exceptions: existing file front matter (e.g. `language: ko`) or explicit user request. No bulk-translate of legacy Korean docs unless asked.

## Trigger

Top-priority operating contract when any appear:

- New feature request
- Bug report
- Test failure
- Refactor request
- Perf/stability improvement request

## Repository routing

**Canonical map (SoT):** [`structure.md`](structure.md) — paths, Django apps, URLs, test layout, doc trees, common commands. **On conflict, structure.md wins.**

| Work type | Persona | Code / docs entry (detail in structure.md) |
|-----------|---------|---------------------------------------------|
| `django` | [Denny](persona/denny.md) | `django_apps/`, `config/` — [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md) |
| `database` | Denny | `django_apps/`, `config/` — `database.md` + `django.md` |
| `solver` | Dominic · Yuri | `django_apps/shapez_solver/` — [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | Gina | `frontend/`, `django_apps/web/` — frontend manuals |
| `tests` | Tess | `tests/`, `harness/validators/` — [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | Denny + invariants | `django_apps/asteroid_lab/` — [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

**Session entry:** [`documents/ai/START_HERE.md`](documents/ai/START_HERE.md)  
**Hexagonal (Phase 2+ stub):** `src/shapez2_factory/` — layers in [`docs/architecture/README.md`](docs/architecture/README.md)

References: [`structure.md`](structure.md) · `@docs/domain/` · `@docs/architecture/` · `@docs/runbooks/` · `@documents/ai/START_HERE.md` · `@.cursor/rules/` · `@.cursor/skills/`

## Reading scope

Read only minimum necessary context.

Default read order:

1. `AGENTS.md`
2. `structure.md`
3. `documents/ai/START_HERE.md`
4. Primary work-type persona/manual
5. Active plan, only when task references one
6. Directly relevant source files
7. Directly relevant tests

No bulk-read of unrelated docs. Open secondary manuals only when change touches that area.

## Manual routing

Pick **one primary** work type + optional secondary. Open **only** matching primary persona + manual ([`documents/ai/manuals/`](documents/ai/manuals/)) by default.

| Work type | Persona | Must read |
|-----------|---------|-----------|
| `django` | [Denny](persona/denny.md) | [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md); models/migrations also [`database.md`](documents/ai/manuals/database.md) |
| `database` | Denny | `database.md` + `django.md` |
| `solver` | Dominic · Yuri | [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | Gina | Web/frontend manuals |
| `tests` | Tess | [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | Denny + invariants | [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

**Denny** owns `django_apps/**` + `config/**`. Hexagonal `src/shapez2_factory/` = Dominic · Yuri · Ada · Gina only.

Personas = routing labels, not roleplay. No stylistic persona output unless asked.

## Required workflow

1. Follow [Reading scope](#reading-scope); restate problem.
2. Plan Mode style: list target files, risks, verification approach.
3. Implement smallest units.
4. After changes, run validation below.
5. Update docs only when change affects public behavior, architecture, command usage, data/model contracts, API/schema/payload contracts, project invariants, or active plan status.
6. No commit, push, PR, merge, or `CLOSED` unless user explicitly asks.
7. End with Caveman six sections ([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17) + Output contract format.

## Goal-Driven Autonomous Development Loop

One concrete goal = complete delivery objective.

Drive through:

> User request → requirement analysis → direction Q&A → written plan/checklist → implementation → tests → failure analysis → fix → rerun → doc update → repeat until checklist complete → final summary report.

Don't stop after only planning. Don't stop after only implementing. Don't stop after first failed test. Failed test/lint/type/runtime error = signal to enter fix loop, not stop.

Loop ends only with: **DONE**, **BLOCKED**, **PARTIAL**.

### Phase 1 — Requirement analysis and direction Q&A

Before implementation, restate:

- What user wants
- Why change needed
- What behavior should change
- What behavior must not change
- Which work type (see [Manual routing](#manual-routing))
- Likely files/modules
- Likely tests/verification commands

Ask direction questions only when answer can't be inferred from: (1) user goal, (2) specs/plans, (3) code, (4) tests, (5) failure logs, (6) repo conventions. No confirmation when next step obvious. Ask smallest set of blocking questions; after answers, continue without re-asking unless new blocker.

### Phase 2 — Written plan and checklist

Before editing code, create/update checklist: Goal · Scope · Non-goals · Behavior contract · Forbidden behavior · Target files · Tests to add/update · Verification commands · Doc updates · Risks.

Small tasks: checklist may live in response only. Non-trivial: write/update active project doc, plan, or report per repo conventions (see [`documents/ai/current_plan.md`](documents/ai/current_plan.md) + `docs/`).

Checklist = execution contract. Continue until every item complete, explicitly skipped with documented reason, or `BLOCKED`.

### Phase 3 — Test oracle policy (loop)

Follow [Test oracle policy](#test-oracle-policy) for oracle sources + forbidden list. In loop, also classify every failure **before editing**:

1. production bug
2. incorrect test setup
3. stale fixture
4. changed contract
5. environment/tooling issue

Django tests verify observable app behavior where possible: request handling, form validation, template output, DB effects, permissions, output contracts. Use Django test framework + pytest tooling (fixtures, parametrization, assertion reporting), but keep oracle grounded in contract above — never derive expected behavior from current implementation.

### Phase 4 — Implementation loop

Smallest safe units. Default loop:

1. Pick next unchecked item.
2. Inspect relevant source + tests.
3. Add/update test if behavior changes.
4. Implement smallest production change.
5. Run focused verification ([Validation commands](#validation-commands)).
6. Pass: mark complete, continue.
7. Fail: read full output, find smallest failing unit, classify failure, fix root cause, rerun same command, continue until green or `BLOCKED`.

No unrelated cleanup. No scope broadening. No rewriting unrelated files. No hiding test output. No pytest output-suppression flags (see [pytest output rules](#pytest-output-rules-required)). No skipping failing check unless skip already documented in policy.

### Phase 5 — Failure recovery loop

Failed command ≠ stopping point. On failure:

1. Read failure output.
2. Find failing unit (one test, one lint rule, one type error, one migration/check error, one runtime path).
3. Find likely root cause.
4. Apply smallest safe fix.
5. Rerun same command.
6. If failure changes, continue from new failure.
7. If same failure remains, try one alternate fix.
8. Continue until command passes, change is `BLOCKED`, or three consecutive fixes fail for same root cause.

Three consecutive fixes fail for same root cause → stop `BLOCKED`, report: failure summary · attempted fixes · suspected cause · recommended next step.

### Phase 6 — Documentation update loop

Update docs when implementation changes any: public behavior · architecture · command usage · data/model contract · API/schema/payload contract · project invariant · active plan status · testing/verification workflow.

No doc update for purely internal edits unless docs become misleading. After updating, verify docs + code don't contradict.

### Phase 7 — Completion gate

Before **DONE**, confirm: every item complete/skipped/blocked · implementation complete · relevant tests added/updated · focused verification passed · broader verification passed when applicable · docs/plan updated when required · no failing check hidden · no expected behavior changed without contract-change doc · no unrelated scope added.

Any required item incomplete → don't report **DONE**.

### Terminal states

- **DONE** — goal implemented, checklist complete, verification passed, docs synced when required, final report lists exact files + commands.
- **BLOCKED** — can't safely continue: missing context can't be inferred · unavailable validation command · environment/tooling failure outside task · high-risk change needing approval · security/permission/environment/CI/deploy change needing approval · destructive operation needing approval · repeated failed fixes for same root cause · unclear contract change.
- **PARTIAL** — useful work done, goal not fully closed, remaining gap stated clearly, next action explicit.

Loop `BLOCKED` format (extends [Failure handling](#failure-handling) with attempt history):

```
BLOCKED:
- missing context:
- risky change:
- attempted fixes:
- current failure:
- recommended next step:
```

### Final summary report

Goal-driven loops close with report below. Superset of [Output contract](#output-contract) (adds `Goal status`); Caveman six sections ([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17) still apply.

```
Goal status:      # DONE | BLOCKED | PARTIAL
Summary:
Checklist result:
Files changed:
Tests added/updated:
Commands run:
Validation:
Docs updated:
Risks / follow-up:
Next action:
```

No completion claim without verification. No "tests passed" unless exact command passed. No omitting failed commands.

### Autonomy boundary

Agent owns requirement-to-verification loop:

- requirement analysis · direction Q&A · checklist creation · implementation · tests · failure analysis · fix/rerun loop · doc updates · final summary report

Agent must not autonomously **commit**, **push**, **open PR**, **merge**, or **mark plan `CLOSED`** unless user explicitly asks for finish, PR, push, merge, or closing. Consistent with [Permissions](#permissions) + [PR finish and closing](#pr-finish-and-closing).

## PR finish and closing

Default:

- No commit, push, PR, merge, or `CLOSED` unless user explicitly asks.
- Allowed without approval: prepare proposed commit message, prepare PR summary, report exact next commands.

When user explicitly asks to finish/open/push/close, run checklist below. Final turn must report PR URL, branch, verification results, CI status, whether `CLOSED` applied.

### Preconditions (do not proceed)

- Large changes needing protocol stage 4 (approval): no push/PR before approval ([`protocols/README.md`](protocols/README.md)).
- Full gate failed, `BLOCKED:`, high-risk change pending, or user asked to keep WIP/draft.

### Checklist (fixed order)

1. **Full gate** — `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .` (all green).
2. **Commit** — Stage only request scope; Conventional Commits style; exclude `.env`, secrets, `var/`, `.pytest_cache`, `.ruff_cache`, other artifacts/cache.
3. **Push** — Feature branch: `git push -u origin HEAD`. No direct push to `main`/`master`, no `--force`, no `--no-verify`.
4. **PR** — Create/update via `gh` (Summary + Test plan). Follow PR body format in [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md).
5. **CI** — On failure, fix + re-push; repeat triage per babysit + [`testing.md`](documents/ai/manuals/testing.md) dual gate.
6. **Closing** — Mark plan item `CLOSED` with date in [`documents/ai/current_plan.md`](documents/ai/current_plan.md); confirm specs/runtime docs match code.

### Merge and approval

- **Default**: Agent prepares publish steps but does not publish.
- **Squash merge / merge to main**: Only when user/reviewer explicitly requests `gh pr merge` or equivalent.

### Stop only when user confirmation is required

- Force push to `main`/`master`, large `pyproject.toml`/CI/deploy config changes, security/permission files.
- Unapproved large features, or explicit instruction to keep draft PR.

## Validation commands

Local pytest default: `powershell -File scripts/test_fast.ps1` (details: [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) § local scripts).

Asteroid Lab Run Solver (no UI): `python manage.py run_solver --slug <slug>` — stack log: `var/log/solver_summary_stack/` ([`01_entry_point.md`](documents/Algorithm/solver_runtime/01_entry_point.md)).

```bash
powershell -File scripts/test_fast.ps1   # daily TDD
ruff check .
mypy django_apps config src
black --check .
```

PR/merge full gate: `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`
On failure, no completion claim; report in `BLOCKED:` format.

### pytest output rules (required)

**No pytest output-suppression flags.**

| Forbidden flag | Reason |
|---|---|
| `-q` / `--quiet` | Hides failure detail |
| `--tb=no` | Removes traceback; hard to debug |
| `--no-header` | Loses context when used alone |
| `-p no:terminal` | Suppresses all output |

Allowed: `-v`, `-s`, `--tb=short` (default), `--tb=long`, `-x`, `--maxfail=N`.

Details + Forbidden shortcuts: [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) § pytest output rules.

## Test oracle policy

User not required to know pytest syntax.

When tests needed, derive oracle from:

- user-provided Given/When/Then
- existing spec
- observed regression
- golden fixture
- public API contract
- database invariant
- security/permission rule
- performance budget

Don't invent expected behavior from current implementation.

Bug fixes:

- Add/identify regression test before production fix.
- Regression test must fail before production fix.
- If it doesn't fail, report it's not a valid regression test.

Forbidden:

- weakening assertions to pass tests
- deleting failing tests
- replacing exact expectations with broad truthiness checks
- changing expected values without classifying as contract change

## Permissions

- Default: read, search, plan
- Allowed writes: source, tests, docs inside workspace
- **PR finish and closing** additionally allows only after explicit user request:
  - `git commit` / `git push` on feature branch
  - `gh pr create`, PR body updates, CI status checks
  - Closing metadata in plan + `documents/ai/current_plan.md`
- User approval required:
  - Environment config (`.env`, large `pyproject.toml` changes)
  - CI/deploy configuration
  - Security/permission files
  - Large rename / delete
- Forbidden:
  - Reading secrets
  - Exposing `.env`, credentials, token files
  - Editing generated artifacts directly
  - Claiming completion without verification
  - **Leading-underscore toggle renames** — only difference is adding/removing leading `_` (`func`↔`_func`, methods, variables, parameters, same-meaning import aliases). No style/lint/"private-public cleanup". Exception: new symbols **required** by approved request, spec, or bug fix.

Details: [`.cursor/rules/shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) Forbidden Shortcuts · [`testing.md`](documents/ai/manuals/testing.md) § Forbidden shortcuts.

## Tools

- Code search: use actively
- Terminal: verification + reproduction only; no destructive commands
- Browser: when UI/visual verification needed
- MCP: only what project configures (see `.cursor/mcp.json`)
- Skills: prefer `@.cursor/skills/` when relevant

## Input contract

Input must be one of:

- Issue/ticket description
- Failure log
- Example of desired behavior
- Reference file or spec document

If info insufficient, state what's missing before implementing.

## Output contract

Always close with:

```
Summary:
Files changed:
Commands run:
Validation:
Risks / follow-up:
Docs updated:
```

If no files changed, write `Files changed: none`.

## Failure handling

Stop rather than force progress when:

- Domain rules conflict
- Validation commands not found
- High regression risk with no baseline test
- High-risk change needs user approval

Stop format:

```
BLOCKED:
- missing context:
- risky change:
- recommended next step:
```

## Security and privacy

- No reading `.cursorignore` targets.
- Never summarize/print sensitive values.
- External tools: minimum permission only.
- No assuming terminal/MCP auto-run outside explicit allowlist.

## Definition of done

- Didn't exceed request scope.
- Narrow verification + (when PR applies) full gate results reported.
- Failed checks explicit; if green + user requested publishing, [PR finish and closing](#pr-finish-and-closing) checklist done or `BLOCKED:` explains why not.
- Docs + code don't contradict.
- When PR applies: URL, branch, CI status (or merge hold reason) in final response.
- Plan item `CLOSED` only when user explicitly requested, or reason closing impossible stated.

## References

- [Persona index](persona/README.md)
- [Protocol pipeline](protocols/README.md)
- [Architecture rules](.cursor/rules/architecture.mdc)
- [Cursor memo](documents/CURSOR_MEMO.md)
