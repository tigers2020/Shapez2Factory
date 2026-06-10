# Project Review Memory

Tracks bounded review runs for periodic project review automation.
Read this file before each run to avoid duplicate work.

## Recovery note (2026-06-10)

Prior automation runs created Linear issues SHA-7 through SHA-29, but this file was missing from the repo at run start. Areas covered by those issues are treated as recently reviewed; do not re-file unless new evidence appears.

---

## 2026-06-10 04:30

Reviewed area:
- path/module/feature: `harness/validators/compare_golden.py`, `tests/golden/`, `tests/golden/README.md`, CI/test scripts (`ci.yml`, `scripts/test_fast.ps1`)

Skipped:
- CI validation gaps (SHA-18, SHA-19, SHA-20 already open)
- Asteroid Lab subprocess/artifact paths (SHA-7–SHA-13, SHA-21–SHA-29)
- Recipe graph validation (SHA-23, SHA-24)
- Shape preview API (SHA-25, SHA-26)

Findings:
- SHA-30: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI

Notes:
- `compare_golden.py` is implemented but only imported from `harness/validators/__init__.py`; zero pytest usage.
- `tests/golden/candidate_selector_trunk_split_{input,expected}.json` exists but no code references the scenario name.
- `tests/golden/README.md` still defers test wiring until after compare_golden exists (stale).
