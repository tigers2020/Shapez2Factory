# shapez2 Factory Planner repository structure

Django-first project: runtime ownership is `config/`, `manage.py`, and `django_apps/`. Tests split into `tests/unit/` and `tests/integration/`.

**Repository map SoT:** This file. [`AGENTS.md`](AGENTS.md) is the agent operating contract and router (work types, gates, manuals) — on path conflicts, **structure.md wins**.

## Documentation layers

| Tree | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | DOX rail — agent operating contract; child `AGENTS.md` per major tree; **not** the path map SoT |
| [`structure.md`](structure.md) | **Repository map SoT** — paths, apps, URLs, tests, commands |
| [`documents/`](documents/) | Domain, architecture, runbook, ADR summaries (agent-friendly) |
| [`documents/`](documents/README.md) | Canonical body text, CANON, plans, research |
| [`src/shapez2_factory/`](src/shapez2_factory/) | Hexagonal solver-core extraction target; Asteroid Lab CLI-first migration in progress ([`documents/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](documents/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md)) — Django-free (BA-1) |

## Top-level layout

| Path | Purpose |
|---|---|
| `AGENTS.md` | DOX rail — root agent contract + Child DOX Index; see also `documents/`, `django_apps/`, `src/`, `documents/`, `.cursor/`, `tests/`, `frontend/` child `AGENTS.md` |
| `structure.md` | Repository map SoT (this document) |
| `documents/` | Domain, architecture, runbook, ADR summaries |
| `config/` | Django settings, root URLs, WSGI/ASGI, runtime flags |
| `django_apps/shapez_core/` | Shape parsing, normalization, preview API |
| `django_apps/shapez_solver/` | Solver projects/runs, recipe graph, macro patterns, planner services |
| `django_apps/asteroid_lab/` | Asteroid Lab ORM/index/cache, artifact ingest, replay/viewer adapters, and Django management wrappers; run-solver request path is CLI subprocess-only |
| `django_apps/game_data/` | Canonical game dump ORM, importers, validators, staff browse |
| `django_apps/web/` | Page templates, static assets, thin views, staff tooling |
| `src/shapez2_factory/` | Hexagonal solver-core (Django-free, BA-1); Asteroid Lab CLI entry + pure run stack live here per the CLI-first plan set |
| `tests/unit/` | Unit tests by app/domain |
| `tests/integration/` | Django request/response, page/API smoke |
| `tests/fixtures/` | Shared test inputs |
| `tests/golden/` | Deterministic regression datasets |
| `tests/support/` | Shared test helpers and contracts |
| `harness/validators/` | Golden comparators (e.g. `compare_golden.py`) |
| `documents/` | Current document authority, plans, research, reports — [`documents/README.md`](documents/README.md) |
| `protocols/` | Multi-step pipeline ([`protocols/README.md`](protocols/README.md)) |
| `persona/` | Position lenses (domain routing — not roleplay) ([`persona/README.md`](persona/README.md)) |
| `documents/knowledge/raw/ai/templates/` | Contract brief + PR plan templates |
| `.cursor/` | Cursor rules, skills, editor guidance |
| `assets/css/` | Tailwind input CSS source |
| `frontend/recipe_graph_editor/` | Vite + React Flow editor source |
| `frontend/graph_layout/` | TypeScript graph layout engine source |
| `locale/` | gettext catalog |
| `scripts/` | Locale build, graph preview, diagnostics helpers |
| `var/` | Local run traces/debug output — not source of truth. Asteroid Lab CLI artifacts live under `var/runs/<run_key>/` (atomic `manifest.json` + `output/replay_core.jsonl`), staging in `var/runs/.tmp/` — see [artifact design spec](documents/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) |

`node_modules/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.graph_preview_cache*/`, `db.sqlite3`, `.env` are local/generated artifacts, not structural canon.

## Django app ownership

### `django_apps/shapez_core/`

- `domain/`: shape primitives, catalog, operations, crystal geometry, shape patterns.
- `services/`: shape code parser, codec, render scene, SVG preview thumbnail, preview response composition.
- `views.py` + `urls.py`: `/api/health/`, `/api/shape-preview/`.

### `django_apps/shapez_solver/`

- `models.py`: persisted solver projects/runs, macro pattern/recipe graph storage.
- `domain/`: operation metadata, factory demand, search cost, and other solver-side domain helpers.
- `services/`: operation engine, recipe graph adapters/validation, planner/scaffold, pattern lab, catalog repository.
- `dto/`: solver-facing DTO.
- Solver UI and related JSON endpoints are served via `django_apps.web` routes.

### `django_apps/asteroid_lab/`

- Asteroid map input, artifact-indexed solver runs, replay tracks, and lab viewer services.
- Run Solver is `subprocess_only`: Django exports game-data snapshot input, invokes `python -m shapez2_factory.interfaces.cli.asteroid_solve`, ingests the finalized artifact, and serves replay from artifact JSONL first with DB cache fallback.
- Does **not** depend on removed `django_apps.shapez_asteroid` or legacy mining layout solver packages (enforced by boundary tests).

### `django_apps/game_data/`

- `models/`: canonical game dump ORM (concrete fields, relations, constraints; no domain `JSONField`).
- `importers/`: deterministic `GameDataImporter` and section importers.
- `services/`: classifiers, identifiers, `validators`, import guards.
- `browse/`: staff browse dashboard (`registry.py`, thin `views.py`, `urls.py`).
- `admin.py`: aggregate-root `ModelAdmin` and inlines aligned with `browse/registry.py` specs.
- Tests: `tests/unit/game_data/`.

### `django_apps/web/`

- `views.py`, `views/`: public pages, gallery, demo, support, asteroid mining lab UI, solver UI, pattern lab, staff macro-pattern flows.
- `services/graph_preview.py`: graph preview asset/cache helper.
- `social_adapter.py`, `socialaccount_forms.py`: django-allauth/social account hooks.
- `templates/web/`: page templates and partials.
- `static/web/`: Tailwind output CSS, JS bundles, solver timeline, GLTF preview, staff scripts, vendor assets.

## URL ownership

Root routing (`config/urls.py`):

| Path | Owner |
|---|---|
| `/admin/game-data/` | `django_apps.game_data.browse` |
| `/admin/` | Django admin |
| `/i18n/` | Django language switching |
| `/accounts/` | django-allauth |
| `/api/` | `django_apps.shapez_core` |

Internationalized routes (`i18n_patterns`, default language without prefix) include `django_apps.web` pages such as `/`, `/gallery/`, `/demo/`, `/support/`, `/asteroid-miner-layout/`, `/solver/`, `/solver/pattern-lab/`, staff macro-pattern URLs, auth shortcuts, `/solve/`, and graph-preview cache URLs.

## Test layout

- `tests/unit/shapez_core/`: parser, render scene, SVG preview, geometry.
- `tests/unit/shapez_solver/`: solver engine, recipe graph, models, catalog, pattern lab.
- `tests/unit/asteroid_lab/`: lab ORM, decode, service boundaries.
- `tests/unit/game_data/`: import, models, admin browse, JSON ban, simulation contracts.
- `tests/unit/architecture/`: Django app import boundaries and repository map governance.
- `tests/unit/web/`: template/markup and web-specific checks.
- `tests/integration/api/`: health/API integration checks.
- `tests/integration/web/`: page smoke, auth, pattern lab, macro-pattern staff flows.

## Documents map

- [`documents/README.md`](documents/README.md): canonical current document index.
- [`documents/index/document_lifecycle.md`](documents/index/document_lifecycle.md): current-only lifecycle definitions.
- [`documents/index/document_inventory.md`](documents/index/document_inventory.md): current authority inventory.
- [`documents/knowledge/raw/ai/`](documents/knowledge/raw/ai/README.md): current plan, context notes, checklist, manuals, active AI plans.
- [`documents/knowledge/raw/algorithm/`](documents/knowledge/raw/algorithm/README.md): Asteroid Lab algorithm authority (`asteroid_lab_11` ACTIVE); stale `documents/Algorithm/` → [`authority-redirect.md`](documents/knowledge/raw/algorithm/authority-redirect.md).
- [`documents/plans/`](documents/plans/): active or not-yet-confirmed implementation plans.
- [`documents/research/`](documents/research/): active research and domain evidence.
- [`documents/reports/`](documents/reports/README.md): observation/debug/audit reports, not canonical contracts.

## Common commands

| Goal | Command |
|---|---|
| Install dev dependencies | `pip install -e ".[dev]"` |
| Run Django locally | `python manage.py runserver` |
| Run tests (default: scope to your change) | `python -m pytest <path-to-test-file-or-dir>` |
| Run full test suite | `python -m pytest` — use before merge/release or when broad regression is needed |
| Run unit tests | `python -m pytest -m unit` |
| Run asteroid lab tests | `python -m pytest tests/unit/asteroid_lab/` |
| Static analysis | `ruff check .` |
| Type-check | `mypy django_apps config src` |
| Format check | `black --check .` |
| Build CSS | `npm run build:css` |
| Build Recipe Graph editor | `npm run build:recipe-graph-editor` |
