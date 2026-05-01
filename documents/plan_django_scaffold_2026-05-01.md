# Plan: Django scaffold

- Date: 2026-05-01
- Status: approved for implementation
- Basis: architect-approved plan `django_scaffold_structure_2566eb51`

## Goal

Create the initial Django scaffold for `shapez2Solver` while keeping the solver core independent from Django.

## Scope

1. Add Python packaging, Django 5.2, pytest, lint, format, and type-check configuration.
2. Create `config/`, `django_apps/projects`, `django_apps/web`, and `django_apps/api`.
3. Create `src/shapez2_solver` with minimal domain, application, and infrastructure placeholders.
4. Add Tailwind CSS v4 input/output paths and npm scripts.
5. Add `SolverProject` and `SolverRun` skeleton models with migrations.
6. Add `/` and `/api/health/` smoke endpoints and tests.

## Non-goals

- Real solver implementation.
- Celery, Redis, Channels, PostgreSQL Docker, DRF/Ninja, Cytoscape.js, or deployment pipeline setup.
- Django-dependent logic inside `src/shapez2_solver`.

## Validation

Run the scaffold harness in this order:

```text
pytest
ruff check .
black --check .
mypy src
```

If `black .` is needed to correct formatting, report the formatting change separately.
