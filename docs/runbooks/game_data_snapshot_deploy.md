# game_data snapshot deploy runbook

**Scope:** Asteroid Lab `game_data` snapshot boundary (ADR-004, v0).  
**Owner:** django (`game_data`) + `web` assembler + `asteroid_lab` adapter.

## Prerequisites

- Application code on the target revision (selectors, snapshot builder, web assembler, solver adapter).
- `documents/game_data/` bundle present with valid `manifest.json`.
- Database on **`default`** alias only (v0: no replica reads for snapshot builds).

## Deploy sequence

### Step 1 — Import and verify manifest

From the repository root:

```bash
python manage.py import_game_data --verify
```

- Imports normalized rows from `documents/game_data` (default `--source`).
- `--verify` ensures the on-disk manifest matches the pinned `ImportBatch` before snapshot consumers run.
- On failure, do not proceed; fix the bundle or re-import with an explicit `--batch-name` per [`django_apps/game_data/management/commands/import_game_data.py`](../../django_apps/game_data/management/commands/import_game_data.py).

### Step 2 — Unit gate (selectors + builder + contracts)

```bash
python -m pytest tests/unit/game_data/test_snapshot_selectors.py tests/unit/game_data/test_snapshot_builder.py tests/unit/asteroid_lab/test_game_data_contracts.py tests/unit/asteroid_lab/test_game_data_snapshot_adapter.py tests/unit/asteroid_lab/test_game_data_coord_transform_golden.py tests/unit/asteroid_lab/test_game_data_snapshot_determinism.py tests/unit/web/test_asteroid_game_data_snapshot.py -q
```

Confirms ordered row tuples, `SnapshotMeta.data_revision`, adapter mapping, and coord golden invariants.

### Step 3 — Integration smoke (solver + snapshot)

```bash
python -m pytest tests/integration/web/test_solver_with_game_data_snapshot.py -q
```

Exercises the cross-app path: `web.services.asteroid_game_data_snapshot` → solver runtime entry with a pinned snapshot.

## Rolling deploy (v0)

- **Read-only consumer path:** snapshot build and solver adapter do not write `game_data` tables at request time.
- **No new migrations** for this integration slice in v0; deploy is code + import batch only.
- Roll out application pods first, then run Step 1 on each environment so `ImportBatch.manifest_self_hash` matches the code revision under test.
- Rollback: revert application revision; prior import batches remain in DB (snapshots pin `data_revision` per batch).

## Related docs

| Doc | Role |
|-----|------|
| [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md) | Import matrix, layer ownership |
| [Asteroid game_data snapshot (domain)](../domain/asteroid_game_data_snapshot.md) | DTO shape, ordering, hash |
| [Asteroid coord transform spec](../domain/asteroid_coord_transform_spec.md) | Server X/Y after decode |
| [Integration plan (Phase 0–5)](../superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md) | Micro-tasks T001–T099 |

## Future: PatternLibrary (deferred)

Do **not** enable in v0 deploy. Follow-up plan (placeholder):

- [`docs/superpowers/plans/2026-XX-XX-asteroid-pattern-library-from-game-data.md`](../superpowers/plans/2026-XX-XX-asteroid-pattern-library-from-game-data.md) — compile `BuildingSnapshot` into PatternLibrary; candidate geometry at build time; miner allowlist from `game_data`.
- Until that ADR/plan ships, `SolverRun.config_json` may record snapshot meta as **provenance only** (not algorithm input).

## PR gate (post-deploy / pre-merge)

```powershell
python -m pytest tests/unit/game_data/test_snapshot_selectors.py tests/unit/game_data/test_snapshot_builder.py tests/unit/asteroid_lab/test_game_data_contracts.py tests/unit/asteroid_lab/test_game_data_snapshot_adapter.py tests/unit/asteroid_lab/test_game_data_coord_transform_golden.py tests/unit/asteroid_lab/test_game_data_snapshot_determinism.py tests/unit/web/test_asteroid_game_data_snapshot.py tests/integration/web/test_solver_with_game_data_snapshot.py -q

python -m ruff check django_apps/game_data/selectors django_apps/game_data/snapshots django_apps/asteroid_lab/optimization/game_data_contracts.py django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py django_apps/web/services/asteroid_game_data_snapshot.py django_apps/asteroid_lab/services/solver_runtime_entry.py

python -m mypy django_apps/game_data django_apps/asteroid_lab django_apps/web

python -m black --check django_apps/game_data/selectors django_apps/game_data/snapshots django_apps/asteroid_lab/optimization/game_data_contracts.py django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py django_apps/web/services/asteroid_game_data_snapshot.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/game_data/test_snapshot_selectors.py tests/unit/game_data/test_snapshot_builder.py tests/unit/asteroid_lab/test_game_data_contracts.py tests/unit/web/test_asteroid_game_data_snapshot.py
```
