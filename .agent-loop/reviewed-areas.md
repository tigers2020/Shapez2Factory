# Project Review Memory

Tracks areas reviewed by periodic project-review automation to prevent duplicate Linear issues.

Bootstrap note: Linear team `shapez2factory` already had issues SHA-7..SHA-43 from prior automation runs before this file existed in-repo.

## 2026-06-10 11:30

Reviewed area:
- path/module/feature: `assets/css/input.css` + `django_apps/web/static/web/css/app.css` + Tailwind `build:css` CI gap (`.github/workflows/ci.yml`, `package.json`, `DESIGN.md`)

Skipped:
- CI validation gaps already filed: SHA-35 (graph-layout), SHA-40 (recipe-graph-editor), SHA-42 (locale), SHA-41 (governance), SHA-19/20 (manage.py check, mypy scope)
- Asteroid Lab replay/ingest areas (SHA-21, SHA-37, SHA-38, SHA-33, etc.)
- Solver layer budget issues (SHA-14, SHA-31, SHA-32)
- Locale strict-mode gap (SHA-43)

Findings:
- SHA-44: CI never runs build:css; committed app.css can drift from Tailwind source

Notes:
- `package.json` `build:css` outputs committed `app.css`; `ci.yml` has no Node/npm step.
- `DESIGN.md` requires `npm run build:css` after template/`@source` changes; production loads committed `app.css` via `base.html`.
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` checks a few lab overlay class substrings in `app.css` but is not a full rebuild drift gate.
- Fresh `npm run build:css` on current tree matches committed `app.css` (md5 `450986bed220fc6a44cda342682a81af`); gap is missing CI enforcement, not current drift.
