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
| `django_apps/shapez_asteroid/` | Asteroid extraction and mining layout optimization app |
| `django_apps/web/` | Templates, static assets, thin views for pages and staff tooling |
| `tests/unit/` | Fast unit tests for core, solver, asteroid, and web behavior |
| `tests/integration/` | Django request/response and page/API integration tests |
| `documents/` | Active plans, research, algorithm specs, game rules, samples, UI references, notes/meta/attribution, AI manuals, and archive indexes. Current map and document comparison: [`documents/README.md`](documents/README.md) |
| `protocols/` | Multi-step pipeline canonical procedure ([`protocols/README.md`](protocols/README.md)) |
| `persona/` | Persona cards and role routing ([`persona/README.md`](persona/README.md)) |
| `.cursor/` | Cursor rules and editor guidance |
| `assets/css/` | Tailwind input CSS source |
| `frontend/recipe_graph_editor/` | Vite + React Flow editor; `npm run build:recipe-graph-editor` writes to `django_apps/web/static/web/js/recipe_graph_editor/` |
| `frontend/graph_layout/` | TypeScript graph layout engine and static bundle sources for solver/editor graph rendering |
| `locale/` | gettext catalogs (for example, `locale/ko/LC_MESSAGES/django*.po`) |
| `package.json` | Root npm scripts: `build:css`, `build:recipe-graph-editor`, and combined frontend build |
| `scripts/` | Ad-hoc tooling such as locale and graph-preview helpers |

Generated or local-only artifacts such as `node_modules/`, `.pytest_cache/`, `.ruff_cache/`,
`.mypy_cache/`, `.graph_preview_cache*/`, `db.sqlite3`, and `.env` are not architectural source of truth.

## Django app ownership

### `django_apps/shapez_core/`

- `domain/`: shape primitives, catalog, operations, crystal geometry, shape patterns.
- `services/`: shape code parser, codec, render scene, SVG preview thumbnails, preview response composition.
- `views.py` + `urls.py`: `/api/health/` and `/api/shape-preview/`.

### `django_apps/shapez_solver/`

- `models.py`: persisted solver projects/runs, macro pattern/recipe graph storage, related entities.
- `domain/`: solver-side domain helpers such as operations metadata, factory demand, and search cost.
- `services/`: operation engine, recipe graph adapters/validation, planner/scaffold services, pattern lab, catalog repositories.
- `dto/`: solver-facing DTOs such as solver graph shapes.
- Solver UI and related JSON are reached via `django_apps.web` (see `django_apps/web/urls.py`), not via a dedicated `/api/solver/` mount in `config/urls.py`.

### `django_apps/shapez_asteroid/`

- `extraction/`: blueprint decoding, grid-coordinate authority, and asteroid extraction DTOs.
- `services/asteroid_mining_layout/`: multi-pass mining layout solver, placement pipeline, routing/recovery logic, trace hooks, and replay/timeline DTOs.
- `ports/`: adapter boundary for solver input/output integration.
- `views.py` + `urls.py`: `/api/asteroid/health/`.

### `django_apps/web/`

- `views.py`: thin controllers for public pages (`/`, gallery, demo, support, asteroid mining, solver UI, pattern lab) and staff macro-pattern flows under `internal/staff/macro-patterns/`.
- `services/graph_preview.py`: graph preview asset/cache helpers used by pages.
- `social_adapter.py`, `socialaccount_forms.py`: django-allauth / social account hooks.
- `templates/web/`: page templates and partials; `templates/account/`, `templates/socialaccount/`, `templates/allauth/` for auth UI overrides.
- `static/web/`: CSS (`static/web/css/app.css` from Tailwind build), JS bundles, solver timeline, GLTF preview, macro pattern staff scripts, and vendor assets.

## URL ownership

Root routing (`config/urls.py`):

- `/admin/`: Django admin.
- `/i18n/`: language switching.
- `/accounts/`: django-allauth (`allauth.urls`).
- `/api/`: `django_apps.shapez_core` (`health/`, `shape-preview/`).
- `/api/asteroid/`: `django_apps.shapez_asteroid` (`health/`).

Internationalized routes (`i18n_patterns`, default language without URL prefix):

- `/jsi18n/`: JavaScript catalog.
- All paths from `django_apps.web` (see `django_apps/web/urls.py`), including `/`, `/gallery/`, `/demo/`, `/support/`, `/asteroid/`, `/solver/`, `/solver/pattern-lab/`, staff macro-pattern URLs under `/internal/staff/macro-patterns/`, auth shortcuts (`/signup/`, `/login/`, `/logout/` redirects), `/solve/` solver page redirect, and `/internal/graph-preview-cache/<filename>` for cached preview assets.

## Test layout

- `tests/unit/shapez_core/`: parser, render scene, SVG preview thumbnails, geometry.
- `tests/unit/shapez_solver/`: solver engine, recipe graph, models, catalog, pattern lab.
- `tests/unit/shapez_asteroid/`: asteroid extraction and mining layout solver services.
- `tests/unit/web/`: template/markup and web-specific unit checks where used.
- `tests/integration/api/`: health and related API checks.
- `tests/integration/web/`: page smoke, auth, pattern lab, macro-pattern staff flows.

## Documents map

- [`documents/README.md`](documents/README.md): canonical document index, active-vs-archive policy, and latest plan/research comparison.
- [`documents/ai/`](documents/ai/README.md): current plan, context notes, checklist, manuals, and AI-side implementation plans.
- [`documents/Algorithm/`](documents/Algorithm/): active asteroid mining solver architecture/spec notes and step-by-step Cursor session briefs.
- [`documents/plans/`](documents/plans/): active or not-yet-confirmed implementation plans.
- [`documents/research/`](documents/research/): active research notes and domain evidence, including grid-coordinate authority.
- [`documents/game_rules/`](documents/game_rules/README.md): shapez 2 domain rules and solver abstractions.
- [`documents/archive/`](documents/archive/README.md): completed, obsolete, or reference-only planning documents.

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests | `python -m pytest` |
| Run tests by marker | `python -m pytest -m unit` / `-m integration` / `-m shapez_solver` / `-m shapez_core` / `-m web` / `-m api` |
| Static analysis | `ruff check .` |
| Type-check | `mypy .` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
| Build Recipe Graph editor | `npm run build:recipe-graph-editor` (or `npm run build` for CSS + editor) |
