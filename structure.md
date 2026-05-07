# shapez2Solver repository structure

This repository is organized as a Django-first project. Runtime ownership lives under
`config/`, `manage.py`, and `django_apps/`, while tests are split by unit vs integration.

## Top-level layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | Contributor/agent routing, quality gate, manual index |
| `config/` | Django project settings, root URLs, WSGI/ASGI |
| `django_apps/shapez_core/` | Shape parsing, normalization, preview API, canonical game data |
| `django_apps/shapez_solver/` | Solver services, recipe/macro models |
| `django_apps/shapez_asteroid/` | Asteroid miner / pump layout optimization (separate app; MIP 등은 후속) |
| `django_apps/web/` | Templates, static assets, thin views (pages + staff tooling) |
| `tests/unit/` | Fast unit tests for core, solver, asteroid, and web behavior |
| `tests/integration/` | Django request/response and page/API integration tests |
| `documents/` | Research (`research/`), plans (`plans/`), progress notes (`notes/`), project meta (`meta/`), attribution (`attribution/`), **game rules** (`game_rules/`), [`archive/`](documents/archive/) (completed sessions: [`archive/2026-05-completed/`](documents/archive/2026-05-completed/README.md)), AI manuals & session notes (`ai/`). Index and document comparison notes: [`documents/README.md`](documents/README.md) |
| `protocols/` | Multi-step pipeline **canonical** procedure ([`protocols/README.md`](protocols/README.md)) |
| `persona/` | Persona cards and role routing ([`persona/README.md`](persona/README.md)) |
| `.cursor/` | Cursor rules and editor guidance |
| `assets/css/` | Tailwind input CSS source |
| `frontend/recipe_graph_editor/` | Vite + React Flow editor; `npm run build:recipe-graph-editor` (via repo `package.json`) → `django_apps/web/static/web/js/recipe_graph_editor/` |
| `frontend/graph_layout/` | TypeScript graph layout engine and static bundle sources for solver/editor graph rendering |
| `locale/` | gettext catalogs (e.g. `locale/ko/LC_MESSAGES/django*.po`) |
| `package.json` | Root npm scripts: `build:css` (Tailwind → `django_apps/web/static/web/css/app.css`), `build:recipe-graph-editor` |
| `scripts/` | Ad-hoc tooling (e.g. `build_locale_ko.py`, `render_graph_preview.mjs`) |

Generated or local-only artifacts such as `node_modules/`, `.pytest_cache/`, `.ruff_cache/`,
`.mypy_cache/`, `.graph_preview_cache*/`, `db.sqlite3`, and `.env` are not part of the architectural source of truth.

## Django app ownership

### `django_apps/shapez_core/`

- `domain/`: shape primitives, catalog, operations, crystal geometry, shape patterns
- `services/`: shape code parser, codec, render scene, SVG preview thumbnails, preview response composition
- `views.py` + `urls.py`: `/api/health/` and `/api/shape-preview/`

### `django_apps/shapez_solver/`

- `models.py`: persisted solver projects/runs, macro pattern/recipe graph storage, related entities
- `domain/`: solver-side domain helpers (e.g. operations metadata, factory demand, search cost)
- `services/`: operation engine, recipe graph adapters/validation, planner/scaffold services, pattern lab, catalog repositories
- `dto/`: solver-facing DTOs (e.g. solver graph shapes)
- Solver UI and related JSON are reached via `django_apps.web` (see `django_apps/web/urls.py`), not via a dedicated `/api/solver/` mount in `config/urls.py`.

### `django_apps/shapez_asteroid/`

- `services/`·`ports/`: (스켈레톤) 향후 MIP·입력·청사진 연동
- `views.py` + `urls.py`: `/api/asteroid/health/`

### `django_apps/web/`

- `views.py`: thin controllers for public pages (`/`, gallery, demo, support, asteroid mining placeholder, solver UI, pattern lab) and **staff** macro-pattern flows under `internal/staff/macro-patterns/`
- `services/graph_preview.py`: graph preview asset/cache helpers used by pages
- `social_adapter.py`, `socialaccount_forms.py`: django-allauth / social account hooks
- `templates/web/`: page templates and partials; `templates/account/`, `templates/socialaccount/`, `templates/allauth/` for auth UI overrides
- `static/web/`: CSS (`static/web/css/app.css` from Tailwind build), JS bundles (Recipe Graph editor build under `static/web/js/recipe_graph_editor/`, solver timeline, GLTF preview, macro pattern staff scripts), vendor assets

## URL ownership

Root routing (`config/urls.py`):

- `/admin/` — Django admin
- `/i18n/` — language switching
- `/accounts/` — django-allauth (`allauth.urls`)
- `/api/` — `django_apps.shapez_core` (`health/`, `shape-preview/`)
- `/api/asteroid/` — `django_apps.shapez_asteroid` (`health/`)

Internationalized routes (`i18n_patterns`, default language without URL prefix):

- `/jsi18n/` — JavaScript catalog
- All paths from `django_apps.web` (see `django_apps/web/urls.py`), including `/`, `/gallery/`, `/demo/`, `/support/`, `/asteroid/`, `/solver/`, `/solver/pattern-lab/`, staff macro-pattern URLs under `/internal/staff/macro-patterns/`, auth shortcuts (`/signup/`, `/login/`, `/logout/` redirects), `/solve/` → solver page redirect, and `/internal/graph-preview-cache/<filename>` for cached preview assets.

## Test layout

- `tests/unit/shapez_core/`: parser, render scene, SVG preview thumbnails, geometry
- `tests/unit/shapez_solver/`: solver engine, recipe graph, models, catalog, pattern lab
- `tests/unit/shapez_asteroid/`: asteroid optimizer API/services (스켈레톤)
- `tests/unit/web/`: template/markup and web-specific unit checks where used
- `tests/integration/api/`: health and related API checks
- `tests/integration/web/`: page smoke, auth, pattern lab, macro-pattern staff flows

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests | `python -m pytest` |
| Run tests (markers) | `python -m pytest -m unit` / `-m integration` / `-m shapez_solver` / `-m shapez_core` / `-m web` / `-m api` (see `pytest.ini`, `tests/conftest.py`) |
| Static analysis | `ruff check .` |
| Type-check | `mypy .` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
| Build Recipe Graph editor | `npm run build:recipe-graph-editor` (or `npm run build` for CSS + editor) |
