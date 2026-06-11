# Manual: Django · Backend

Before starting work, review [`AGENTS.md`](../../../AGENTS.md) Core Rules.

## Ownership

| App | Path | Responsibility |
|----|------|------|
| shapez_core | `django_apps/shapez_core/` | Shape rules · parsing · normalization |
| shapez_solver | `django_apps/shapez_solver/` | Solver use cases · services |
| asteroid_lab | `django_apps/asteroid_lab/` | Asteroid Lab (ORM · decode · replay; separate from recipe solver) |
| web | `django_apps/web/` | Templates · static assets · thin views |
| game_data | `django_apps/game_data/` | Game dump ORM · importer · admin · browse |

Persona: [`persona/denny.md`](../../../persona/denny.md). Path glob rules: [`.cursor/rules/django-apps.mdc`](../../../.cursor/rules/django-apps.mdc).

### `game_data` layout

| Path | Responsibility |
|------|------|
| `models/` | Concrete fields · FK/OneToOne · `Meta.constraints` (domain models) |
| `importers/` | Deterministic JSON → ORM import |
| `services/` | Classification · validation · `validators.assert_no_domain_json_fields` |
| `browse/` | Taxonomy → admin dashboard (thin view) |
| `admin.py` | Aggregate root `ModelAdmin` · inlines |
| `management/commands/import_game_data.py` | CLI import + post-import guards |

Browse URL: `config/urls.py` → `path("admin/game-data/", include("django_apps.game_data.browse.urls"))`.

**Domain-complete coverage** (A vs B, manifest, shape provenance, Phase 2 audit pending): [`docs/domain/game_data_coverage.md`](../../../docs/domain/game_data_coverage.md).

## No domain JSON (`game_data`)

- **No `JSONField`** on domain models (prevents schema-less dumps).
- Field names `raw_json`, `payload`, `data`, `source_dump`, `audit_blob` are **forbidden**.
- Exception: model name must be listed in `ALLOWED_JSON_MODELS` and only after **plan · ADR approval** ([`validators.py`](../../../django_apps/game_data/services/validators.py), [`test_no_raw_json_domain_storage.py`](../../../tests/unit/game_data/test_no_raw_json_domain_storage.py)).
- Legacy fields such as `audit_blob` must be **migrated to concrete tables**; do not leave them on runtime models.

## Blueprint grid coordinates (shared)

Blueprint copy grids have **no column where `X == 0`** (`1` and `-1` are adjacent east–west; `0` is non-transit). Server code `(x, y)` also **cannot have `x == 0`**. Details · rationale: [`research_blueprint_grid_coordinates_2026-05-10.md`](../../research/research_blueprint_grid_coordinates_2026-05-10.md).

## Dependency direction (do not violate)

- `shapez_core` → **no import** of `web`, `shapez_solver`, `asteroid_lab`
- `shapez_solver` → only `shapez_core` allowed · **no import** of `web` · `asteroid_lab`
- `asteroid_lab` → only `shapez_core` allowed (future) · may be unused in skeleton · **no import** of `web` · `shapez_solver`
- `web` → `shapez_core`, `shapez_solver`, `asteroid_lab`, `game_data` allowed
- `game_data` → **no import** of `web`, `shapez_solver`, `asteroid_lab` (only `shapez_core` allowed, future)
- `shapez_core` · `shapez_solver` · `asteroid_lab` → **no import** of `game_data`

Mechanical verification: [`tests/unit/architecture/test_django_app_import_boundaries.py`](../../../tests/unit/architecture/test_django_app_import_boundaries.py).

Canonical source: [`.cursor/rules/architecture.mdc`](../../../.cursor/rules/architecture.mdc).

## Views · endpoints

- HTTP endpoints belong in the **app that owns the behavior**.
- Keep views thin: domain · solver rules go in `services/` · `importers/` · use cases ([Denny](../../../persona/denny.md) · Rule 1 below).

## References (external — for Django work)

The canonical sources for this repo are [`.cursor/rules/django-apps.mdc`](../../../.cursor/rules/django-apps.mdc) + this manual. The following are **supplementary**; on conflict, repo rules · import matrix · `game_data` JSON ban take precedence.

| Topic | Link | Use in this repo |
|------|------|-------------------|
| Cursor modular rules · thin views · query/migration/testing habits | [Cursor Rules for Django (DEV)](https://dev.to/olivia_craft/cursor-rules-for-django-the-complete-guide-to-ai-assisted-django-development-3je5) | Same split as `.cursor/rules/*.mdc`; 30-line view smell · `select_related` · service layer align with Denny checklist |
| Object-level permissions · predicate · `ObjectPermissionBackend` | [django-rules — Using rules with Django](https://github.com/dfunckt/django-rules#using-rules-with-django) | When introducing **new** staff/API object permissions: align `rules` app · backend config · `rules.add_perm` / `Model` `Meta.rules_permissions` patterns to this doc. Current repo is django-allauth + `LoginRequiredMixin` / `@staff_member_required` focused |

**DEV guide ↔ repo mapping (summary)**

- Rule 1 (fat models / thin views) → [django-apps.mdc](../../../.cursor/rules/django-apps.mdc) Thin view section
- Rule 2 (query discipline) → review `select_related` / `prefetch_related` on list/admin/browse querysets
- Rule 3–4 (migrations, settings) → [`database.md`](database.md), [`environment.md`](environment.md)
- Rule 5 (testing) → [`testing.md`](testing.md), `tests/unit/<app>/`
- Modular rules → `django-apps.mdc` + [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) (per-app glob)

## Run

```bash
python manage.py runserver
```

Install: from repo root, `pip install -e ".[dev]"`.

Environment variable classification · `.env` / `.env.debug` layering: [`environment.md`](environment.md).

## Authentication

`django-allauth`, `accounts/` URLs. OAuth clients are registered via environment · `SocialApp`, not in code.

## Read next

- Models · migrations: [`database.md`](database.md)
- Solver logic: [`solver.md`](solver.md)
