# ADR-004: game_data Snapshot Boundary for Asteroid Lab

- **Status**: Accepted
- **Date**: 2026-05-21
- **Owner**: django + asteroid_lab integration

## Context

Asteroid Lab consumes normalized building and transport data from the `game_data`
Django app without breaking app-layer import boundaries.

- `asteroid_lab` must not import `game_data` directly.
- Solver-facing code must not hold `QuerySet` instances or ORM model objects.
- Cross-app assembly is required at a boundary that can pin a deterministic data
  revision.

## Decision

1. `game_data` selectors and snapshot builders own read-only ORM access.
2. `web/services/asteroid_game_data_snapshot.py` is the sole cross-app assembler.
3. `asteroid_lab/adapters/game_data_snapshot_adapter.py` maps snapshot DTOs into
   Asteroid Lab enums and structures without importing `game_data`.
4. `SnapshotMeta.data_revision` is set from the pinned import batch manifest hash.
5. The v0 database policy uses only the `default` DB alias.
6. Snapshot `content_hash` is calculated from the canonical solver-relevant DTO
   subset only. Build timestamps are excluded from reproducibility keys.
7. Snapshot bodies are boundary data, not permission to revive deleted solver
   algorithms. New algorithmic consumers need a new accepted ADR.

## Consequences

- Solver-facing code stays free of Django ORM and import-matrix violations.
- Snapshot builds are reproducible by row ordering and data revision pinning.
- Direct `asteroid_lab` to `game_data` imports require an ADR amendment and an
  explicit import-boundary test update.
- Presentation metadata remains outside this snapshot until a separate
  presentation snapshot contract exists.

## References

- Import matrix test: `tests/unit/architecture/test_django_app_import_boundaries.py`
- Asteroid Lab invariants: `.cursor/rules/asteroid-lab-invariants.mdc`
- Django app layering: `documents/ai/manuals/django.md`
- ADR template: `docs/adr/ADR-0000-template.md`
