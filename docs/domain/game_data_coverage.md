# game_data — Domain-Complete Coverage

**Status:** Phase 0–1 + 1d + 3 + **Phase 2 simulation path audit** (2026-05-22)  
**Spec:** [`docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md`](../superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md)  
**JSON types (Tier A):** [`game_data_json_structure.md`](game_data_json_structure.md)  
**ADR:** [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md) (Asteroid solver subset only)

## Principles

```text
Domain-complete ≠ lossless mirror.
Provenance is never overwritten.
Manifest owns coverage classification.
ADR-004 snapshot remains explicit subset only.
```

## A vs B backup boundary

| Tier | Path | Role |
| ---- | ---- | ---- |
| **A** | `documents/game_data/` | Full interchange source (runtime reflection JSON); schema: [game_data_json_structure.md](game_data_json_structure.md) |
| **B** | `game_data_backup/` (`dumpdata`) | Normalized ORM restore snapshot |

**Regenerate Tier B** (after schema/import changes; local SQLite):

```powershell
$env:DJANGO_USE_SQLITE = "1"
python manage.py migrate game_data
python manage.py flush --no-input
python manage.py import_game_data --source documents/game_data
python manage.py seed_game_data_taxonomy
python manage.py dumpdata game_data --indent 2 -o game_data_backup/game_data_dump.json
python manage.py import_game_data --verify
```

B is ORM-shaped, not a structural copy of A. Re-run only when normalized models or import semantics change.

- `flush` wipes **all** SQLite tables in `db.sqlite3` (local dev only), including taxonomy seeded by migration `0016`.
- `seed_game_data_taxonomy` rebuilds `GameDataNamespace` / `GameDataSection` from model `verbose_name_plural` labels (same rules as migration `0016`, plus sub-table prune aligned with migrations `0020` and `0023` — includes `ShapeRecipeSourceAppearance`). Run **after import** and **before** `dumpdata` so Tier B restores admin browse navigation.
- `loaddata` alone does **not** re-import from Tier A; use `import_game_data` when refreshing from `documents/game_data`.
- Migration `0025` may delete `ToolbarElement` rows with null `tree_node` before enforcing non-null FK (dev DB only; importer always sets `tree_node`).
- `ArtifactChecksum` proves **A files matched import inputs**, not that every nested leaf became an ORM row.
- **B is not** a byte-for-byte backup of A.
- **B is** a **domain-complete** projection when every registered nested path is `promoted`, `cross_ref`, or `ignore_audit`.

### pytest (unit)

- Full bundle seed: `game_data_backup/game_data_dump.json` via `loaddata` only (`tests/unit/game_data/fixtures.py`).
- Tier A import / verify / dump regeneration: **manual CI / release gate** — [`game_data_tier_a_release_gate.md`](../runbooks/game_data_tier_a_release_gate.md). Not part of `test_fast`.
- Slice importer unit tests may use `tests/fixtures/game_data/*.json` (not `documents/game_data/`).

### Tier B audit (ORM vs dump, 2026-05-22)

After regenerate, **every non-empty `game_data` table** in SQLite must match `game_data_dump.json` row counts (`dumpdata` omits zero-row models).

| Check | Expected |
| ----- | -------- |
| Populated models in dump | **57** (55 import tables + `GameDataNamespace` + `GameDataSection` after seed) |
| Fixture records (typical) | ~34.9k rows |
| `ShapeRecipe.catalog_source` | absent (Phase 1d) |
| `ShapeRecipeSourceAppearance.catalog_source` | present on appearance rows only |
| `definition_snapshot` as ORM field | absent (`UnknownProperty` paths only) |
| `import_game_data --verify` | manifest hash matches latest `ImportBatch` |

**Zero-row tables (normal after import; often absent from dump):**

| Model | Why empty |
| ----- | --------- |
| `GameDataReference` | Unresolved cross-refs only; current bundle resolves inline |
| `LocalizedMessage` | Not populated by `import_game_data` (admin/schema scaffold) |
| `ResearchGlobalConfig` | Not populated by `import_game_data` |
| `LazyLocalizedPlaceholderReplacement` | Created only when lazy text refs carry placeholders |

Taxonomy rows are **non-empty** when `seed_game_data_taxonomy` ran before `dumpdata`.

**pytest:** `-q` / `--quiet` / `--tb=no` **금지** ([`documents/ai/manuals/testing.md`](../../documents/ai/manuals/testing.md)). 긴 `game_data` 스위트는 `-v` 또는 기본 출력으로 실패·진행을 보이게 한다 (~300 tests, ~70s).

## Coverage manifest disposition

Registry: `django_apps/game_data/coverage/manifest.py`

| Disposition | Meaning |
| ----------- | ------- |
| `promoted` | Normalized ORM rows + `SourceObject` / FK cross-refs |
| `cross_ref` | FK or flatten equivalence (e.g. toolbar `Children` → row paths) |
| `ignore_audit` | `UnknownProperty` with `reason_code` (no domain `JSONField`) |

Success criterion:

```text
∀ registered paths p in MANIFEST:
  exactly one disposition applies after import
```

Phase 2 adds paths only after audit review — not before.

## Items provenance (P1)

**No `Item` model.** `items.json` rows normalize to `ShapeRecipe` geometry plus appearances.

| Model | Role |
| ----- | ---- |
| `ShapeRecipe` | Canonical geometry — **UK `(operation_uid, shape_hash)`** |
| `ShapeRecipeSourceAppearance` | Per-artifact row lineage — **UK `(import_batch, artifact_filename, source_row_index)`** |

Invariants:

```text
ShapeRecipe = canonical geometry
ShapeRecipeSourceAppearance = source lineage
catalog_source must not exist on ShapeRecipe (removed Phase 1d)
```

Import order: `shapes.json` (FULL) then `items.json` (ITEMS). Overlap (70 rows) keeps **both** appearances; ITEMS import must not delete FULL provenance.

`ShapeRecipe.source_object` = primary row for browse convenience: first FULL appearance’s `SourceObject`, else first ITEMS. **Truth** remains on `ShapeRecipeSourceAppearance`.

Tests: `tests/unit/game_data/test_shape_recipe_provenance.py`

## Toolbar flatten equivalence

- Source: 204 flat rows; `display_name_key` = tree path.
- Nested `Children[]` in snapshots are **not** mirrored as 519 extra nodes.
- Proof: path closure, parent/child edges, no dangling parents, DAG acyclicity.

Tests: `tests/unit/game_data/test_toolbar_closure.py`, `tests/unit/game_data/test_toolbar_tree.py`

## Assembly reflection ignore policy

- `buildings.json` / `building_groups.json`: `Assembly` / `DeclaredMembers` under `definition_snapshot` are **reflection metadata**.
- Importer records bounded `UnknownProperty` rows with `reason_code=REFLECTION_METADATA`, `classification=assembly_reflection`.
- **No** `DeclaredMembers` domain tables.

Tests: `tests/unit/game_data/test_building_assembly_audit.py`

## Simulation (C-lite + audit-first)

Already promoted (examples): `ConnectableSimulation`, connectors, lanes, bounds, belt policy.

Delegate / factory / backing-field paths: `ignore_audit` via `UnknownProperty` and parameter registry — not primary domain tables.

## ADR-004 snapshot subset boundary

| Consumer | May use |
| -------- | ------- |
| `game_data/snapshots/builder` + `AsteroidGameDataSnapshot` | Buildings, transport registry (v0 contract) |
| Browse / admin / coverage tests | Full domain-complete ORM |

**Do not** add `ShapeRecipeSourceAppearance`, simulation deep state, or toolbar trees to the solver snapshot without ADR + contract version bump.

## Phase 2 — simulation_systems.json (closed at audit scope)

**Scope note:** Phase 2 “closed” means **priority audit TSV** paths (`_nested_path_audit_priority.tsv`) are manifest-classified and tested — not every path in the full ~5.7k-path aggregate TSV. Unlisted paths may still receive `ignore_audit` via `classify_norm_path` fallbacks at import time.

Audit artifacts:

| File | Role |
| ---- | ---- |
| `documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv` | Full normalized path aggregate |
| `documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv` | Review subset (`--normalized --priority`) |

Registry: `django_apps/game_data/coverage/simulation_paths.py` + `MANIFEST.update(manifest_entries_from_rules())`.

Import audit: `sync_definition_snapshot_coverage_audit` records bounded `UnknownProperty` rows for `definition_snapshot` ignore paths.

| Path family | Disposition | `reason_code` |
| ----------- | ----------- | ------------- |
| `simulation_parameters.ConnectableSimulations` (+ Connectors, Lanes, Bounds) | `promoted` | ORM tables |
| `ConnectableSimulations[].Building` | `cross_ref` | `BuildingVariant` |
| `ConnectableSimulations[].InputLanes` | `cross_ref` | lane importer alias |
| `definition_snapshot.*ChainPositions*` / `*TileBasedSystems*` (delegate tree) | `ignore_audit` | `RUNTIME_DELEGATE` |
| `ConnectableSimulations[].Junctions*` / `Simulation.State` / `NextBundle` | `ignore_audit` | `RUNTIME_DELEGATE` |
| `Interlock.*` / `*k__BackingField*` / `Assembly` / CLR type lists | `ignore_audit` | `REFLECTION_METADATA` |
| `ISimulationSystem.*` / `SimulationFactory.*` | `ignore_audit` | `RUNTIME_DELEGATE` / `SIMULATION_FACTORY_STUB` |

**No new ORM** for `ChainPositions` (planner graph uses `ConnectableSimulations` import path).

Tests: `tests/unit/game_data/test_simulation_path_coverage.py`

```text
simulation_systems.json priority nested paths: promoted | cross_ref | ignore_audit (proven at Phase 2 scope).
```

## References

- Plan: [`docs/superpowers/plans/2026-05-22-game-data-domain-complete-coverage.md`](../superpowers/plans/2026-05-22-game-data-domain-complete-coverage.md)
- Reason codes: `django_apps/game_data/coverage/reason_codes.py`
- Import: `django_apps/game_data/importers/shape_recipes.py`
