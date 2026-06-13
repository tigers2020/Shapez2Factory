# Validation Routine

Canon commands: `AGENTS.md` § Validation. This doc defines **when** to run them — not every line edit needs the full gate.

## Summary

Match validation to **workflow strictness** (`workflow-strictness.md`). PR push always tier 4.

```text
Read-only: none
Tiny / docs-only: minimum for touched scope
Normal slice done: related bundle + lint on touched scope
High-risk before commit: tier 3 (tier 3+ for solver/replay)
Before PR: tier 4 (manage.py check + test_fast.ps1)
Before merge: GitHub CI
```

Do not run the full suite on every one-line change.

## Strictness mapping

| Strictness | Before commit (minimum) |
|------------|-------------------------|
| Read-only | none |
| Tiny — docs only | markdown/link check; `check_governance.ps1` if governance touched |
| Tiny — copy / 1-file | targeted test or grep; ruff/black on touched file if Python |
| Normal — Python fix | related pytest + ruff/black on touched paths |
| Normal — feature slice | tier 2 |
| High-risk / solver / replay | tier 3+; golden loop when applicable |
| PR push (any) | tier 4 |

## Tier 1 — Small edits in progress

Examples: rename a variable, adjust one type, tweak one condition.

```powershell
ruff check path/to/changed_file.py
black --check path/to/changed_file.py
pytest path/to/relevant_test.py -q
```

Skip pytest mid-edit if the slice is incomplete.

## Tier 2 — Feature slice complete

Examples: `source_adapter.py` change plus its tests are done.

```powershell
ruff check .
black --check .
pytest tests/unit/asteroid_lab/layers/ -q
pytest tests/unit/asteroid_lab/experiments/ -q
```

Scope pytest to the subsystem you touched when possible.

## Tier 3 — Before commit

Run before commit for **High-risk** and large Normal slices:

```powershell
ruff check .
black --check .
mypy django_apps config src
pytest <relevant-test-paths> -q
```

For large solver / accounting changes (e.g. L4/L5 routing), run the relevant layer unit tests under `tests/unit/asteroid_lab/layers/` plus stack-runner smoke tests.

## Tier 4 — Before PR push

Release gate — run the canonical set from `AGENTS.md`:

```powershell
python manage.py check
ruff check .
black --check .
mypy django_apps config src
powershell -File scripts/test_fast.ps1
```

Optional when time allows:

```powershell
pytest -m integration -n auto
```

PR/full merge prep: `scripts/test_full.ps1` plus lint/type/format. Solver smoke: `python manage.py run_solver --slug <slug>`.

## Verification evidence (required in final report)

Every pass claim must include:

| Field | Example |
|-------|---------|
| command | `pytest tests/unit/asteroid_lab/layers/ -q` |
| exit code | `0` |
| key output | `18 passed` |
| changed files | `django_apps/asteroid_lab/...` |
| skipped / not run | reason if any tier skipped |

```text
Verification:
- pytest tests/unit/asteroid_lab/layers/ -q → exit 0 (18 passed)
- ruff check . → exit 0
```

Golden loop: include command, config flags, output paths, diagnostics summary.

## Agent rules

- Never claim pass without running the tier that matches the work state.
- Never relax or skip tests to force green.
- Workflow docs reference `AGENTS.md` § Validation only — link here for timing, not alternate commands.
