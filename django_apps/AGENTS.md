# django_apps AGENTS.md

## Scope

Django runtime adapters: ORM, views, services, management commands, templates, and request/index/cache boundaries.

## Rules

- Root `AGENTS.md` stays authority for workflow, publish, validation, and conflict handling.
- Keep views and management commands thin; put domain behavior in services or model methods.
- Use Django ORM. Raw SQL needs a current contract reason and focused tests.
- Avoid N+1 with `select_related` / `prefetch_related` where query shape can fan out.
- Do not move solver authority from `src/shapez2_factory/` into Django apps.
- Do not add raw JSON/blob domain storage unless current canon explicitly allows it.
- Preserve public function/class signatures unless the user asks to change them.

## Verify

- Focused app tests under `tests/unit/<app>/` or matching integration tests.
- For broad Django changes, run `python manage.py check` plus the relevant gates in root `AGENTS.md`.
