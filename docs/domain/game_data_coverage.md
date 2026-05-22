# game_data — Domain-Complete Coverage

**Status:** Phase 0–1 + 1d + 3 documented (2026-05-22)  
**Spec:** [`docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md`](../superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md)  
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
| **A** | `documents/game_data/` | Full interchange source (runtime reflection JSON) |
| **B** | `game_data_backup/` (`dumpdata`) | Normalized ORM restore snapshot |

- `ArtifactChecksum` proves **A files matched import inputs**, not that every nested leaf became an ORM row.
- **B is not** a byte-for-byte backup of A.
- **B is** a **domain-complete** projection when every registered nested path is `promoted`, `cross_ref`, or `ignore_audit`.

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

## Phase 2 pending — audit review required

**Do not** classify these as `promoted` or `ignore_audit` in the manifest until a human reviews `scripts/audit_simulation_nested_paths.py` output.

Pending paths (from initial audit sample — not final):

| Path (sample) | Notes |
| ------------- | ----- |
| `definition_snapshot.ChainPositions` | High list volume; domain vs runtime TBD |
| `definition_snapshot.TileBasedSystems` | Related conveyor/tile capture |
| `definition_snapshot.*.Simulations` | Nested under converter snapshots |
| `simulation_parameters.ISimulationSystem.*` | Delegate — likely `ignore_audit` |

Output target (when run): `documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv`

After review: update `coverage/manifest.py` and add parity tests before any new ORM promotion.

## References

- Plan: [`docs/superpowers/plans/2026-05-22-game-data-domain-complete-coverage.md`](../superpowers/plans/2026-05-22-game-data-domain-complete-coverage.md)
- Reason codes: `django_apps/game_data/coverage/reason_codes.py`
- Import: `django_apps/game_data/importers/shape_recipes.py`
