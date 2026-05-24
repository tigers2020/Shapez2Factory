# AGENTS.md

## Mission

This repository targets **shapez2 Factory Planner**.
Always follow **small safe changes + fast verification + documentation sync**.

## Communication language

| Surface | Language |
|---|---|
| Chat with the user (questions, plans, reviews, closing summaries) | **Korean** (한국어) |
| Repository docs (`docs/`, `documents/`, ADRs, runbooks, specs, plans) | **English** |
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
**Hexagonal (Phase 2+ stub):** `src/shapez2_factory/` — layers in [`docs/architecture/README.md`](docs/architecture/README.md)

References: [`structure.md`](structure.md) · `@docs/domain/` · `@docs/architecture/` · `@docs/runbooks/` · `@documents/ai/START_HERE.md` · `@.cursor/rules/` · `@.cursor/skills/`

## Manual routing

Pick **one** work type, then open **only** the matching persona and manual ([`documents/ai/manuals/`](documents/ai/manuals/)).

| Work type | Persona | Must read |
|-----------|---------|-----------|
| `django` | [Denny](persona/denny.md) | [`documents/ai/manuals/django.md`](documents/ai/manuals/django.md); for models/migrations also [`database.md`](documents/ai/manuals/database.md) |
| `database` | Denny | `database.md` + `django.md` |
| `solver` | Dominic · Yuri | [`solver.md`](documents/ai/manuals/solver.md) |
| `frontend` / `graph UI` | Gina | Web/frontend-related manuals |
| `tests` | Tess | [`testing.md`](documents/ai/manuals/testing.md) |
| `asteroid_lab` | Denny + invariants | [`asteroid-lab-invariants.mdc`](.cursor/rules/asteroid-lab-invariants.mdc) |

**Denny** owns `django_apps/**` and `config/**`. Hexagonal `src/shapez2_factory/` is Dominic · Yuri · Ada · Gina only.

## Required workflow

1. Read relevant `docs/domain/`, `docs/architecture/`, `AGENTS.md`, and code; restate the problem.
2. In Plan Mode style, list target files, risks, and verification approach.
3. Implement in the smallest possible units.
4. After changes, run the validation steps below.
5. When behavior or design changes, update `docs/` and the active plan.
6. When scope is closed and narrow verification is green, run [PR finish and closing](#pr-finish-and-closing-agent-owned) without waiting for the user to ask.
7. End with the Caveman six sections ([`shapez2-core.mdc`](.cursor/rules/shapez2-core.mdc) §17) and the Output contract format.

## PR finish and closing (agent-owned)

When implementation and narrow verification are done and scope is closed, the agent completes the steps below even if the user did not say “open PR”, “finish”, or “closing”. The final turn must report PR URL, verification results, and whether `CLOSED` was applied.

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

- **Default**: Agent owns PR open, CI green, and closing docs.
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

## Permissions

- Default: read, search, plan
- Allowed writes: source, tests, and docs inside the workspace
- **PR finish and closing** additionally allows (when preconditions and checklist are met, without a separate user request):
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
- Failed checks are explicit; if green, [PR finish and closing](#pr-finish-and-closing-agent-owned) checklist is done or `BLOCKED:` explains why not.
- Docs and code do not contradict each other.
- When a PR applies: URL, branch, and CI status (or merge hold reason) appear in the final response.
- Relevant plan item is `CLOSED`, or the reason closing was not possible is stated.

## References

- [Persona index](persona/README.md)
- [Protocol pipeline](protocols/README.md)
- [Architecture rules](.cursor/rules/architecture.mdc)
- [Cursor memo](documents/CURSOR_MEMO.md)
