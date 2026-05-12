# Research: shapez_core solver plan compatibility

> **Archived 2026-05-01.** Describes a `src/shapez2_solver/` layout; repository boundary is now `django_apps/shapez_core` and `django_apps/shapez_solver`.

## Scope

- Target document: `../../meta/shapez_core_solver_dev_plan.md`
- Goal: check whether the plan fits the current repository as-is, and identify the minimum changes needed to make it usable
- Date: 2026-05-01

## Sources reviewed

- `AGENTS.md`
- `.cursor/rules/architecture.mdc`
- `protocols/README.md`
- `pyproject.toml`
- `config/settings.py`
- `django_apps/projects/models.py`
- `django_apps/web/views.py`
- `django_apps/web/urls.py`
- `tests/test_project_models.py`
- `tests/test_web_smoke.py`
- `src/shapez2_solver/domain/shape.py`
- `src/shapez2_solver/application/solver_service.py`
- `../../meta/shapez_core_solver_dev_plan.md`

## Current project baseline

- The repository is a Django scaffold plus a small pure-Python solver core.
- Django apps currently present are `django_apps.projects`, `django_apps.web`, and `django_apps.api`.
- The Python package under `src/shapez2_solver/` currently contains `domain`, `application`, and `infrastructure`.
- The active database configuration is SQLite, not MySQL.
- The current web contract includes a live `/gallery/` page and smoke tests that assert gallery content.

## Compatibility summary

Verdict: the plan is directionally useful, but not compatible with the current repository without revision.

The document is strongest when it describes domain ownership:

- shape parsing and validation should not live inside a gallery-only feature
- solver input should move toward normalized structures rather than raw strings
- rendering should consume normalized data instead of owning parsing logic

The document becomes incompatible when it assumes a different application topology than the repository already has.

## Confirmed mismatches

### 1. App split mismatch

The plan assumes new Django apps named `shapez_core` and `shapez_solver`.

Current repository state:

- Django apps are `projects`, `web`, and `api`
- solver domain code already exists in `src/shapez2_solver/`

Impact:

- adopting the plan literally would require either a major app reorganization or duplicated responsibilities across Django apps and the pure-Python package

### 2. Layer mismatch

The architecture rule defines a layered package rooted at `src/shapez2_solver/` with boundaries like `domain`, `application`, `adapters`, `interfaces`, and `bootstrap`.

Current repository state:

- `src/shapez2_solver/` currently uses `domain`, `application`, and `infrastructure`
- the plan places domain and services inside a Django app tree such as `django_apps/shapez_core/domain/` and `django_apps/shapez_core/services/`

Impact:

- the plan does not align with the repository's preferred direction that domain logic should live in the core package rather than inside Django app-local service folders

### 3. Persistence mismatch

The plan assumes MySQL as a first-class requirement.

Current repository state:

- `config/settings.py` uses SQLite
- `pyproject.toml` does not include MySQL driver dependencies

Impact:

- the plan's database section and phase exit criteria are not immediately compatible
- MySQL can still be a future deployment choice, but it should not be the baseline requirement for the next implementation phase

### 4. Solver boundary mismatch

The plan expects the solver to receive ORM-backed `ShapePattern` objects or objects derived directly from them.

Current repository state:

- `SolverService` takes a pure domain object, `ShapeCode`
- the solver core is currently not coupled to Django ORM

Impact:

- a good adaptation is to introduce normalized DTOs inside `src/shapez2_solver/application` and let Django adapters translate database rows into those DTOs
- directly shifting the solver entrypoint to Django models would weaken the current package boundary

### 5. Web terminology mismatch

The plan says the previous gallery framing should be replaced.

Current repository state:

- `/gallery/` is an implemented route
- the current web UI and tests explicitly assert gallery terminology and structure

Impact:

- replacing gallery naming may still be correct later, but it is not a drop-in change
- this must be treated as an intentional web product rename, not as a harmless wording cleanup

## What should be kept

- The domain ownership principle
- The parser and validator responsibility split
- The normalized shape representation idea
- The rule that rendering consumes normalized data
- The idea that admin or persistence data should not become the solver domain boundary
- The broad testing categories for parser, validation, and solver integration

## What should be changed

### Replace `shapez_core` app ownership with package-first ownership

Recommended adaptation:

- put parsing, validation, normalization, and solver DTOs under `src/shapez2_solver/`
- treat Django models as persistence adapters rather than as the domain home

### Keep Django app changes incremental

Recommended adaptation:

- extend `django_apps.projects` or add one focused new Django app only if persistence is needed
- avoid simultaneous introduction of `shapez_core`, `shapez_solver`, and rendering app splits unless there is a strong operational reason

### Make storage backend neutral in the plan

Recommended adaptation:

- write the plan so it works on SQLite in development and tests
- mention MySQL only as an optional production target if the team decides to adopt it later

### Preserve solver purity

Recommended adaptation:

- keep `SolverService` operating on pure Python DTOs
- add a mapper from Django models to those DTOs in the adapter layer when database-backed patterns arrive

### Treat gallery rename as a separate product decision

Recommended adaptation:

- do not bundle parser/domain work together with gallery renaming
- if the team later wants `Pattern Inspector`, create a separate approved web plan and migrate tests with it

## Recommended compatible target shape

The most compatible next-step architecture is:

- `src/shapez2_solver/domain/`: shape primitives and invariants
- `src/shapez2_solver/application/`: parser, validator orchestration, normalized DTOs, solver-facing contracts
- `src/shapez2_solver/adapters/` or current equivalent: persistence and framework translation code
- `django_apps.projects`: optional project/run storage and later optional pattern storage
- `django_apps.web`: current web UI, kept separate from parser ownership
- `django_apps.api`: API surface, if shape parsing needs exposure later

## Final assessment

`../../meta/shapez_core_solver_dev_plan.md` should not be executed as the active implementation plan for this repository.

It should instead be treated as:

- a useful concept note for domain ownership, and
- an input source for a repository-compatible rewrite

The next safe step is to create a new plan document that preserves the domain ideas while aligning with the repository's existing package boundaries, SQLite baseline, and current Django app layout.
