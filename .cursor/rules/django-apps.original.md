---
description: "Django runtime ownership — Denny persona, thin views, game_data contracts (MUST when editing matched globs)"
globs:
  - django_apps/**
  - config/**
  - manage.py
alwaysApply: false
---

# Django apps (MUST)

Persona: [denny.md](mdc:persona/denny.md). Manual: [django.md](mdc:documents/ai/manuals/django.md). Migrations & models: [database.md](mdc:documents/ai/manuals/database.md).

**External references (repo canonical docs take precedence):** [DEV — Cursor Rules for Django](https://dev.to/olivia_craft/cursor-rules-for-django-the-complete-guide-to-ai-assisted-django-development-3je5) · [django-rules — Using rules with Django](https://github.com/dfunckt/django-rules#using-rules-with-django) — detailed mapping in [django.md § References](mdc:documents/ai/manuals/django.md).

Changes under `django_apps/**` and `config/**` are owned by **Denny**. Hexagonal `src/shapez2_factory/` is Dominic · Yuri · Ada · Gina.

## MUST before editing

1. `@persona/denny.md`, `@documents/ai/manuals/django.md`
2. For models/migrations: `@documents/ai/manuals/database.md`
3. For `game_data`: `@django_apps/game_data/services/validators.py`, `tests/unit/game_data/`

## Forbidden shortcuts

- `JSONField`, `raw_json`, `audit_blob`, `payload`, `data`, `source_dump` on domain models — forbidden without `ALLOWED_JSON_MODELS` and plan approval ([validators.py](mdc:django_apps/game_data/services/validators.py))
- Implementing contract changes without plan and approval
- Do not skip `test_no_raw_json_domain_storage`, `test_admin_browse` when touching `game_data`, browse, admin, or importer
- Cross-app imports that violate the [django.md](mdc:documents/ai/manuals/django.md) import matrix

## Thin view

- HTTP and URLs belong to the app that owns the behavior (`game_data.browse` → `config/urls.py` include).
- Views delegate to services/importers/registry; templates display only.

## Verification

```bash
python -m pytest tests/unit/<app>/   # narrow scope; do not use -q / --quiet / --tb=no
python -m ruff check <paths>
python -m mypy django_apps config src
```

Closing: [shapez2-core.mdc](mdc:.cursor/rules/shapez2-core.mdc) Caveman six sections.
