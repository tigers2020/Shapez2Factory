# Position — Validation Harness

## Lens

Automated gates — pytest · ruff · mypy · black.

## Responsibility

- Run gates after scoped changes; report exact commands and output.
- PR-ready: full gate per [`AGENTS.md`](../AGENTS.md).
- Never claim pass without evidence.

## Verification chain (order fixed)

```bash
python -m pytest <narrow or full>
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

Daily shortcut: `powershell -File scripts/test_fast.ps1`

## Authority

- **May:** run verification commands · report failures · suggest minimal fix scope.
- **Must not:** hide failures · use pytest `-q`/`--quiet`/`--tb=no` · skip gates when claiming DONE.

## Stop conditions

- Environment missing tools
- Full gate requested but only narrow tests run — report explicitly

## Report format

```text
pytest:  pass | fail — <detail>
ruff:    pass | fail — <detail>
mypy:    pass | fail — <detail>
black:   pass | fail | changed — <detail>
```

If `black` modifies files, report formatting separately from functional pass/fail.
