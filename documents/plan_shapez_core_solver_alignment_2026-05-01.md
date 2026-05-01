# Plan: align shape core solver work with current repository

## Basis

- Research: `documents/research_shapez_core_solver_plan_compatibility_2026-05-01.md`
- Input concept: `documents/shapez_core_solver_dev_plan.md`
- Repository rules: `AGENTS.md`, `.cursor/rules/architecture.mdc`, `protocols/README.md`

## Goal

Convert the useful ideas from `shapez_core_solver_dev_plan.md` into a repository-compatible implementation path without forcing an immediate rewrite of the current Django scaffold.

## Decision

We will not adopt the original plan literally.

We will adopt only the compatible principles:

- shape parsing and validation belong to core domain/application code, not to gallery-only UI
- solver inputs should move toward normalized pure-Python DTOs
- Django models and web pages should consume or store normalized data through adapters
- the current `projects`, `web`, and `api` app layout remains the baseline unless a later approved plan justifies a split

## Proposed implementation direction

### 1. Core package first

Primary ownership stays under `src/shapez2_solver/`.

Planned target areas:

- `src/shapez2_solver/domain/`
  - shape primitives
  - value objects
  - domain invariants
- `src/shapez2_solver/application/`
  - parser entrypoints
  - validator orchestration
  - normalization service
  - solver-facing DTOs
- `src/shapez2_solver/adapters/` or equivalent future replacement of `infrastructure/`
  - Django model mappers
  - YAML or database-backed reference data loaders

### 2. Django remains an adapter layer

Near-term Django role:

- `django_apps.projects`
  - keep current solver project and run storage
  - optionally add pattern persistence later if needed
- `django_apps.web`
  - keep current web pages and gallery behavior unchanged unless separately approved
- `django_apps.api`
  - expose parse or solve endpoints later if needed

This keeps ORM models from becoming the solver's domain boundary.

### 3. Database strategy

Baseline:

- keep SQLite as the default development and test database

Optional later decision:

- document MySQL support only if there is a concrete deployment need

This avoids coupling the next phase to infrastructure that the repository does not currently require.

## Proposed phased roadmap

### Phase 1. Normalize solver-side shape input

Scope:

- replace the current raw `ShapeCode`-only path with richer pure-Python DTOs
- define normalized quadrant/layer/pattern structures in the core package

Likely targets:

- `src/shapez2_solver/domain/shape.py`
- `src/shapez2_solver/application/solver_service.py`
- new parser/DTO modules under `src/shapez2_solver/application/`

Exit criteria:

- solver can receive a normalized pure-Python pattern object
- no Django dependency is introduced into the solver entrypoint

### Phase 2. Parser and validator in the core package

Scope:

- implement parser and validator services under `src/shapez2_solver/application/`
- load canonical shape/color data from a repository-controlled source first

Possible data source options:

1. YAML-backed master data in `src/shapez2_solver/infrastructure/game_data/`
2. hard-coded constants in the core package for the initial MVP

Exit criteria:

- valid patterns parse into normalized DTOs
- invalid patterns return explicit errors
- tests cover grammar, empty quadrants, and stacked layers

### Phase 3. Django persistence adapter for patterns

Scope:

- if persistence is needed, introduce pattern storage in a way that maps into core DTOs
- avoid making ORM models the only legal solver input shape

Likely target:

- extend `django_apps.projects` first, unless a focused new app is approved

Exit criteria:

- stored patterns can be converted into normalized DTOs
- solver still runs on pure Python contracts

### Phase 4. Web and admin integration

Scope:

- add inspection or management UI only after parser/domain pieces are stable
- treat `Pattern Inspector` naming as a separate explicit UI decision

Exit criteria:

- UI reads normalized data instead of reparsing raw strings in JavaScript
- any rename from `gallery` is separately approved and reflected in tests

## Non-goals for this plan

- Immediate migration from SQLite to MySQL
- Immediate renaming or removal of the current gallery page
- Major Django app split into `shapez_core` and `shapez_solver`
- Coupling solver entrypoints directly to Django ORM models

## Risks

- If we store normalized shapes only in Django models, the solver boundary will drift toward framework coupling.
- If we rename the gallery while doing parser work, we will mix domain refactoring with UI churn.
- If we require MySQL now, we will slow down implementation with infrastructure work that does not unblock the parser or solver core.

## Approval checkpoint

Before implementation, the human reviewer should confirm:

1. parser and normalization will live under `src/shapez2_solver/`, not inside a new `shapez_core` Django app
2. SQLite remains the default until a separate DB decision is approved
3. gallery rename or replacement is out of scope for the first parser/solver-core implementation pass
