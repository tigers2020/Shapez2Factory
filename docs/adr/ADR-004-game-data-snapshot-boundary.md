# ADR-004: game_data snapshot boundary for Asteroid Lab

- **Status**: Accepted
- **Date**: 2026-05-21
- **Owner**: django + asteroid_lab integration (Phase 0)

## Context

Asteroid Lab must consume normalized building and transport data from the `game_data` Django app without breaking existing architectural guardrails.

- The Django app import matrix **forbids** `asteroid_lab` → `game_data`. This is enforced by `tests/unit/architecture/test_django_app_import_boundaries.py` and must remain true unless this ADR is amended and the matrix test is updated.
- The solver hot path must not hold `QuerySet` instances or ORM model objects. That requirement is documented in `.cursor/rules/asteroid-lab-invariants.mdc` and was reinforced by external architecture review (2026-05-21).
- Cross-app assembly is therefore required at a boundary that respects the matrix while still delivering deterministic, revision-pinned snapshots into the solver.

## Decision

1. **`game_data/selectors`** plus **`game_data/snapshots/builder`** own read-only ORM access. They materialize **ordered row tuples** (stable sort keys, no nested mutables on the consumer path).
2. **`web/services/asteroid_game_data_snapshot.py`** is the sole cross-app assembler. It imports both `game_data` and `asteroid_lab` (permitted by the matrix) and builds frozen **`asteroid_lab.contracts.game_data_snapshot`** DTOs.
3. **`asteroid_lab/adapters/game_data_snapshot_adapter.py`** maps those DTOs into solver-facing enums and structures. It performs **no ORM** access and does not import `game_data`.
4. **`SnapshotMeta.data_revision`** is set to **`ImportBatch.manifest_self_hash`** of the pinned import batch for the snapshot build.
5. **v0 database policy**: only the **`default`** DB alias is used. Replica reads are **forbidden** until revision pinning and a replica lag policy are specified and tested.

## Consequences

### Positive

- Solver code stays free of Django ORM and import-matrix violations.
- Snapshot builds are reproducible: row ordering and `data_revision` pin a single manifest generation.
- Clear ownership: selectors/builder in `game_data`, assembly in `web`, consumption in `asteroid_lab`.

### Negative / constraints

- Adding a direct `asteroid_lab` → `game_data` import requires **this ADR to be amended** and **`test_django_app_import_boundaries.py`** (or equivalent matrix test) to be updated deliberately.
- Presentation metadata (e.g. sprites) is **excluded** from `SolverSnapshot` until a separate **`PresentationSnapshot`** split is specified in domain docs and ADR.

### Trade-offs

- v0 accepts single-primary-DB latency and availability; replica offload is deferred rather than guessed.
- An extra hop (`web` assembler) adds a module but preserves the import matrix without reflection hacks.

## References

- Implementation plan: [`docs/superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md`](../superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md)
- Import matrix test: `tests/unit/architecture/test_django_app_import_boundaries.py`
- Asteroid Lab invariants: `.cursor/rules/asteroid-lab-invariants.mdc`
- Django app layering: `documents/ai/manuals/django.md`
- ADR template (this directory): [`ADR-0000-template.md`](ADR-0000-template.md)
