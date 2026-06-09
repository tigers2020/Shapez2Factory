# Validation Routine

Canon commands: `AGENTS.md` § Validation. This doc defines **when** to run them — not every line edit needs the full gate.

## Summary

```text
While editing: changed files + relevant tests only
Feature slice done: related test bundle + lint/format on touched scope
Before commit: ruff + black + mypy + related tests (always)
Before PR: full fast gate (manage.py check + test_fast.ps1)
Before merge: GitHub CI
```

Do not run the full suite on every one-line change. Do run the commit gate before every commit.

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

Always run before commit:

```powershell
ruff check .
black --check .
mypy django_apps config src
pytest <relevant-test-paths> -q
```

For large solver / accounting changes (e.g. L4/L5 routing), add golden loop:

```powershell
python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy
python scripts/summarize_golden_loop_diagnostics.py
```

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

## Agent rules

- Never claim pass without running the tier that matches the work state.
- Never relax or skip tests to force green.
- Handoff docs and Hermes checklists reference `AGENTS.md` § Validation only — link here for timing, not alternate commands.
