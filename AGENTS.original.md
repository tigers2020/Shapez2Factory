# AGENTS.md

## Mission

This repository targets **shapez2 Factory Planner**.
Always follow **small safe changes + fast verification + documentation sync**.

## Communication language

| Surface | Language |
|---|---|
| Chat with the user (questions, plans, reviews, closing summaries) | **Korean** (한국어) |
| Repository docs (`documents/`, `documents/`, ADRs, runbooks, specs, plans) | **English** |
| Code (identifiers, comments, docstrings), commit messages, PR title/body | **English** |

Exceptions: follow an existing file’s declared front matter (e.g. `language: ko`) or an explicit user request for that artifact; do not bulk-translate legacy Korean docs unless asked.

## Trigger

Use this document as the top-priority operating contract when any of the following appear:

- New feature request
- Bug report
- Test failure
- Refactor request
- Performance or stability improvement request

## Repository routing

**Canonical repository map (SoT):** [`structure.md`](structure.md) — paths, Django apps, URLs, test layout, document trees, and common commands. **On conflict, structure.md wins.**

| Work type | Persona | Code / docs entry (detail in structure.md) |
|-----------|---------|---------------------------------------------|
| `django` | [Denny](persona/denny.md) | `django_apps/`, `config/` — [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md) |
| `database` | Denny | `django_apps/`, `config/` — `database.md` + `django.md` |
| `solver` | Dominic · Yuri | `django_apps/shapez_solver/` — [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | Gina | `frontend/`, `django_apps/web/` — frontend manuals |
| `tests` | Tess | `tests/`, `harness/validators/` — [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | Denny + invariants | `django_apps/asteroid_lab/` — [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

**Session entry:** [`documents/ai/START_HERE.md`](documents/ai/START_HERE.md)  
**Hexagonal (Phase 2+ stub):** `src/shapez2_factory/` — layers in [`documents/architecture/README.md`](documents/architecture/README.md)

References: [`structure.md`](structure.md) · `@documents/domain/` · `@documents/architecture/` · `@documents/runbooks/` · `@documents/ai/START_HERE.md` · `@.cursor/rules/` · `@.cursor/skills/`

## Reading scope

Read only the minimum necessary context.

Default read order:

1. `AGENTS.md`
2. `structure.md`
3. `documents/ai/START_HERE.md`
4. Primary work-type persona/manual
5. Active plan, only when the task references one
6. Directly relevant source files
7. Directly relevant tests

Do not bulk-read unrelated docs. Open secondary manuals only when the change touches that area.

## Manual routing

Pick **one primary** work type and optional secondary work types. Open **only** the matching primary persona and manual ([`documents/ai/manuals/`](documents/ai/manuals/)) by default.

| Work type | Persona | Must read |
|-----------|---------|-----------|
| `django` | [Denny](persona/denny.md) | [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md); for models/migrations also [`database.md`](documents/ai/manuals/database.md) |
| `database` | Denny | `database.md` + `django.md` |
| `solver` | Dominic · Yuri | [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | Gina | Web/frontend-related manuals |
| `tests` | Tess | [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | Denny + invariants | [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

**Denny** owns `django_apps/**` and `config/**`. Hexagonal `src/shapez2_factory/` is Dominic · Yuri · Ada · Gina only.

Personas are routing labels, not roleplay. Do not add stylistic persona output unless asked.

## Required workflow

1. Follow [Reading scope](#reading-scope); restate the problem.
2. In Plan Mode style, list target files, risks, and verification approach.
3. Implement in the smallest possible units.
4. After changes, run the validation steps below.
5. Update docs only when the change affects public behavior, architecture, command usage, data/model contracts, API/schema/payload contracts, project invariants, or active plan status.
6. Do not commit, push, open PRs, merge, or mark plan items `CLOSED` unless the user explicitly asks.
7. End with the Caveman six sections ([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17) and the Output contract format.

## Goal-Driven Autonomous Development Loop

When the user gives one concrete goal, treat it as a complete delivery objective.

Drive the work through:

> User request → requirement analysis → direction Q&A → written plan/checklist → implementation → tests → failure analysis → fix → rerun → document update → repeat until the checklist is complete → final summary report.

Do not stop after only planning. Do not stop after only implementing. Do not stop after the first failed test. A failed test, lint error, type error, or runtime error is a signal to enter the fix loop, not a reason to stop.

The loop ends only with one of: **DONE**, **BLOCKED**, **PARTIAL**.

### Phase 1 — Requirement analysis and direction Q&A

Before implementation, analyze the goal and restate:

- What the user wants
- Why the change is needed
- What behavior should change
- What behavior must not change
- Which work type applies (see [Manual routing](#manual-routing))
- Which files or modules are likely involved
- Which tests or verification commands are likely required

Ask direction questions only when the answer cannot be inferred from: (1) the user's goal, (2) existing specs/plans, (3) existing code, (4) existing tests, (5) failure logs, (6) repository conventions. Do not ask for confirmation when the next step is obvious. When questions are needed, ask the smallest possible set of blocking questions; after the answers arrive, continue without re-asking unless a new blocker appears.

### Phase 2 — Written plan and checklist

Before editing code, create or update a written checklist covering: Goal · Scope · Non-goals · Behavior contract · Forbidden behavior · Target files · Tests to add or update · Verification commands · Documentation updates · Risks.

For small tasks the checklist may live in the response only. For non-trivial tasks, write or update the active project document, plan, or report per repository conventions (see [`documents/ai/current_plan.md`](documents/ai/current_plan.md) and `documents/`).

The checklist is the execution contract. Implementation continues until every checklist item is complete, explicitly skipped with a documented reason, or `BLOCKED`.

### Phase 3 — Test oracle policy (loop)

Follow the existing [Test oracle policy](#test-oracle-policy) for oracle sources and the forbidden list. In the loop, additionally classify every failure **before editing**:

1. production bug
2. incorrect test setup
3. stale fixture
4. changed contract
5. environment/tooling issue

Django tests should verify observable application behavior where possible: request handling, form validation, template output, database effects, permissions, and output contracts. Use Django's test framework and pytest tooling (fixtures, parametrization, assertion reporting), but keep the oracle grounded in the contract above — never derive expected behavior from the current implementation.

### Phase 4 — Implementation loop

Implement in the smallest safe units. Default loop:

1. Pick the next unchecked checklist item.
2. Inspect relevant source and tests.
3. Add or update the test if behavior changes.
4. Implement the smallest production change.
5. Run focused verification ([Validation commands](#validation-commands)).
6. If verification passes: mark the item complete and continue.
7. If verification fails: read the full output, identify the smallest failing unit, classify the failure, fix the root cause, rerun the same command, and continue until green or `BLOCKED`.

Do not switch to unrelated cleanup. Do not broaden scope. Do not rewrite unrelated files. Do not hide test output. Do not use pytest output-suppression flags (see [pytest output rules](#pytest-output-rules-required)). Do not skip a failing check unless the skip is already documented in project policy.

### Phase 5 — Failure recovery loop

A failed command is not a stopping point. When a command fails:

1. Read the failure output.
2. Identify the failing unit (one test, one lint rule, one type error, one migration/check error, one runtime path).
3. Identify the likely root cause.
4. Apply the smallest safe fix.
5. Rerun the same command.
6. If the failure changes, continue from the new failure.
7. If the same failure remains, attempt one alternate fix.
8. Continue until the command passes, the change is `BLOCKED`, or three consecutive fixes fail for the same root cause.

If three consecutive fixes fail for the same root cause, stop with `BLOCKED` and report: failure summary · attempted fixes · suspected cause · recommended next step.

### Phase 6 — Documentation update loop

Update documents when the implementation changes any of: public behavior · architecture · command usage · data/model contract · API/schema/payload contract · project invariant · active plan status · testing or verification workflow.

Do not update docs for purely internal edits unless the docs would otherwise become misleading. After updating, verify that docs and code do not contradict each other.

### Phase 7 — Completion gate

Before reporting **DONE**, confirm: every checklist item is complete, explicitly skipped, or blocked · implementation is complete · relevant tests were added or updated · focused verification passed · broader verification passed when applicable · documents/plan were updated when required · no known failing check is hidden · no expected behavior was changed without contract-change documentation · no unrelated scope was added.

If any required item is incomplete, do not report **DONE**.

### Terminal states

- **DONE** — the requested goal is implemented, checklist is complete, verification passed, docs are synced when required, and the final report lists exact files and commands.
- **BLOCKED** — progress cannot safely continue because of missing context that cannot be inferred · unavailable validation command · environment/tooling failure outside the task · high-risk change requiring approval · security/permission/environment/CI/deploy change requiring approval · destructive operation requiring approval · repeated failed fixes for the same root cause · unclear contract change.
- **PARTIAL** — useful work was completed, the original goal could not be fully closed, the remaining gap is clearly stated, and the next action is explicit.

Loop `BLOCKED` format (extends the [Failure handling](#failure-handling) format with attempt history):

```
BLOCKED:
- missing context:
- risky change:
- attempted fixes:
- current failure:
- recommended next step:
```

### Final summary report

For goal-driven loops, close with the report below. It is a superset of the [Output contract](#output-contract) (adds `Goal status`); the Caveman six sections ([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17) still apply.

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

Do not claim completion without verification. Do not claim tests passed unless the exact command passed. Do not omit failed commands.

### Autonomy boundary

The agent owns the requirement-to-verification loop:

- requirement analysis · direction Q&A · checklist creation · implementation · tests · failure analysis · fix/rerun loop · documentation updates · final summary report

The agent must not autonomously **commit**, **push**, **open a PR**, **merge**, or **mark a plan `CLOSED`** unless the user explicitly asks for finish, PR, push, merge, or closing. This is consistent with [Permissions](#permissions) and [PR finish and closing](#pr-finish-and-closing).

## PR finish and closing

Default:

- Do not commit, push, open PRs, merge, or mark `CLOSED` unless the user explicitly asks.
- Allowed without approval: prepare a proposed commit message, prepare a PR summary, and report exact next commands.

When the user explicitly asks to finish, open, push, or close the task, run the checklist below. The final turn must report PR URL, branch, verification results, CI status, and whether `CLOSED` was applied.

### Preconditions (do not proceed)

- Large changes requiring protocol stage 4 (approval): no push/PR before approval ([`protocols/README.md`](protocols/README.md)).
- Full gate failed, `BLOCKED:`, high-risk change pending, or user explicitly asked to keep WIP/draft.

### Checklist (fixed order)

1. **Full gate** — `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .` (all green).
2. **Commit** — Stage only request scope; Conventional Commits style; exclude `.env`, secrets, `var/`, `.pytest_cache`, `.ruff_cache`, and other artifacts/cache.
3. **Push** — Feature branch: `git push -u origin HEAD`. No direct push to `main`/`master`, no `--force`, no `--no-verify`.
4. **PR** — Create or update via `gh` (Summary + Test plan). Follow PR body format in [`documents/ai/manuals/cursor_usage.md`](documents/ai/manuals/cursor_usage.md).
5. **CI** — On failure, fix and re-push; repeat triage per babysit and [`testing.md`](documents/ai/manuals/testing.md) dual gate.
6. **Closing** — Mark the relevant plan item `CLOSED` with date in [`documents/ai/current_plan.md`](documents/ai/current_plan.md); confirm specs/runtime docs match code.

### Merge and approval

- **Default**: Agent prepares publish steps but does not publish.
- **Squash merge / merge to main**: Only when the user or reviewer explicitly requests `gh pr merge` or equivalent.

### Stop only when user confirmation is required

- Force push to `main`/`master`, large `pyproject.toml`/CI/deploy config changes, security/permission files.
- Unapproved large features, or explicit instruction to keep a draft PR.

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
On failure, do not claim completion; report in `BLOCKED:` format.

### pytest output rules (required)

**Do not use pytest output-suppression flags.**

| Forbidden flag | Reason |
|---|---|
| `-q` / `--quiet` | Hides failure detail |
| `--tb=no` | Removes traceback; hard to debug |
| `--no-header` | Loses context when used alone |
| `-p no:terminal` | Suppresses all output |

Allowed: `-v`, `-s`, `--tb=short` (default), `--tb=long`, `-x`, `--maxfail=N`.

Details and Forbidden shortcuts: [`documents/ai/manuals/testing.md`](documents/ai/manuals/testing.md) § pytest output rules.

## Test oracle policy

The user is not required to know pytest syntax.

When tests are needed, derive the oracle from:

- user-provided Given/When/Then
- existing spec
- observed regression
- golden fixture
- public API contract
- database invariant
- security or permission rule
- performance budget

Do not invent expected behavior from the current implementation.

For bug fixes:

- Add or identify a regression test before the production fix.
- The regression test must fail before the production fix.
- If it does not fail, report that it is not a valid regression test.

Forbidden:

- weakening assertions to make tests pass
- deleting failing tests
- replacing exact expectations with broad truthiness checks
- changing expected values without classifying the work as a contract change

## Permissions

- Default: read, search, plan
- Allowed writes: source, tests, and docs inside the workspace
- **PR finish and closing** additionally allows only after explicit user request:
  - `git commit` / `git push` on a feature branch
  - `gh pr create`, PR body updates, CI status checks
  - Closing metadata in plan and `documents/ai/current_plan.md`
- User approval required:
  - Environment config (`.env`, large `pyproject.toml` changes)
  - CI/deploy configuration
  - Security/permission files
  - Large rename / delete
- Forbidden:
  - Attempting to read secrets
  - Exposing `.env`, credentials, or token files
  - Editing generated artifacts directly
  - Claiming completion without verification
  - **Leading-underscore toggle renames** — changes where the only difference is adding/removing a leading `_` (`func`↔`_func`, methods, variables, parameters, same-meaning import aliases). Do not do this for style, lint, or “private/public cleanup”. Exception: new symbols **required** by an approved request, spec, or bug fix.

Details: [`.cursor/rules/shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) Forbidden Shortcuts · [`testing.md`](documents/ai/manuals/testing.md) § Forbidden shortcuts.

## Tools

- Code search: use actively
- Terminal: verification and reproduction only; no destructive commands
- Browser: when UI/visual verification is needed
- MCP: only what the project configures (see `.cursor/mcp.json`)
- Skills: prefer `@.cursor/skills/` when relevant

## Input contract

Input must be one of:

- Issue/ticket description
- Failure log
- Example of desired behavior
- Reference file or spec document

If information is insufficient, state what is missing before implementing.

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

Stop rather than forcing progress when:

- Domain rules conflict
- Validation commands cannot be found
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

- Do not read `.cursorignore` targets.
- Never summarize or print sensitive values.
- External tools: minimum permission only.
- Do not assume terminal/MCP auto-run outside an explicit allowlist.

## Definition of done

- Did not exceed request scope.
- Narrow verification and (when PR applies) full gate results are reported.
- Failed checks are explicit; if green and the user requested publishing, [PR finish and closing](#pr-finish-and-closing) checklist is done or `BLOCKED:` explains why not.
- Docs and code do not contradict each other.
- When a PR applies: URL, branch, and CI status (or merge hold reason) appear in the final response.
- Relevant plan item is `CLOSED` only when the user explicitly requested closing, or the reason closing was not possible is stated.

## References

- [Persona index](persona/README.md)
- [Protocol pipeline](protocols/README.md)
- [Architecture rules](.cursor/rules/architecture.mdc)
- [Cursor memo](documents/CURSOR_MEMO.md)
