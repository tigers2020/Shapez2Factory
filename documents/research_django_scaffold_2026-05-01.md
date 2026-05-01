# Django scaffold research

- Date: 2026-05-01
- Scope: initial Django scaffold for the shapez2 factory planner.
- Source: `documents/chat.md` and the approved Cursor plan `django_scaffold_structure_2566eb51`.

## Findings

- The project should use Django for web, persistence, templates, and API boundaries.
- Solver and planner logic should remain in a pure Python package under `src/shapez2_solver`.
- Django 5.2 LTS is the baseline for the scaffold (`django>=5.2,<6.0`).
- Tailwind CSS v4 should be built from `assets/css/input.css` into `django_apps/web/static/web/css/app.css`.
- Celery, Redis, Channels, PostgreSQL Docker, Cytoscape.js, and the real solver are out of scope for this scaffold.

## Implementation Notes

- `django_apps/` is used instead of `apps/` to make the Django app boundary explicit.
- `SolverRun.input_snapshot` is required so past runs remain reproducible after a project is edited.
- `SolverProject.solver_settings` avoids naming collisions with `django.conf.settings`.
- `assets/` is treated as a source-only directory and is not included in `STATICFILES_DIRS`.
