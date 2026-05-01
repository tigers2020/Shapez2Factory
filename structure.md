# shapez2Solver repository structure

This repository is now organized as a Django-first project. Runtime ownership lives under
`config/`, `manage.py`, and `django_apps/`, while tests are split by unit vs integration.

## Top-level layout

| Path | Purpose |
|---|---|
| `config/` | Django project settings, root URLs, WSGI/ASGI |
| `django_apps/shapez_core/` | Shape parsing, normalization, preview API, canonical game data |
| `django_apps/shapez_solver/` | Solver services and persisted solver project/run models |
| `django_apps/web/` | Templates, static assets, and page-rendering views |
| `tests/unit/` | Fast unit tests for core and solver behavior |
| `tests/integration/` | Django request/response and page/API integration tests |
| `documents/` | Research, plans, and implementation notes |
| `assets/css/` | Tailwind input CSS source |

Generated or local-only artifacts such as `node_modules/`, `.pytest_cache/`, `.ruff_cache/`,
`.mypy_cache/`, and `db.sqlite3` are not part of the architectural source of truth.

## Django app ownership

### `django_apps/shapez_core/`

- `domain/`: shape primitives, quadrant/layer normalization, catalog constants
- `services/`: shape code parser, render scene builder, preview response composition
- `infrastructure/game_data/`: versioned YAML game data
- `views.py` + `urls.py`: `/api/health/` and `/api/shape-preview/`

### `django_apps/shapez_solver/`

- `models.py`: `SolverProject`, `SolverRun`, `SolverRunStatus`
- `services/`: planner and solver service scaffolds
- `dto/`: solver-facing DTO namespace for future expansion

### `django_apps/web/`

- `views.py`: thin page controllers for `/`, `/gallery/`, `/demo/`
- `templates/web/`: page templates and shared partials
- `static/web/`: CSS, JS, vendor assets, screenshots, and template images

## URL ownership

- `/` -> `django_apps.web`
- `/gallery/` -> `django_apps.web`
- `/demo/` -> `django_apps.web`
- `/api/health/` -> `django_apps.shapez_core`
- `/api/shape-preview/` -> `django_apps.shapez_core`
- `/api/solver/` -> reserved for future `django_apps.shapez_solver` endpoints

## Test layout

- `tests/unit/shapez_core/`: parser and render-scene behavior
- `tests/unit/shapez_solver/`: solver model/service behavior
- `tests/integration/api/`: health and preview endpoint checks
- `tests/integration/web/`: page rendering and asset smoke tests

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests | `pytest` |
| Static analysis | `ruff check .` |
| Type-check | `mypy .` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
