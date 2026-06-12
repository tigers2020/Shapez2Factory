---
title: Building Variants
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [buildings, game-data-analysis]
sources:
  - documents/knowledge/raw/analysis/building_variants/00_summary.md
  - documents/knowledge/raw/game-data-docs/building_variants.schema.txt
confidence: high
---

# Building Variants

## Source

`documents/game_data/building_variants.json` — ~3.8 MB, 131 variant rows. Unity v2 `runtime_reflection` dump (manifest hash in raw analysis).

## What a variant is (source)

Each array element = one **internal building variant**: placement geometry + connectors + footprint for a specific implementation (rotation/mirror family).

| Metric | Value |
|--------|-------|
| Total variants | **131** |
| `*InternalVariant` naming | 128 |
| Mirrored-only (`*Mirrored`) | 34 |
| Embedded in `building_groups` by `Id.Name` | 97 |
| Connector count 0 | 1 (`LabelDefaultInternalVariant`) |

## Envelope (uniform 131/131)

`stable_id`, `source_guid` (= `definition_snapshot.Id.Name`), `display_name_key`, empty `building_stable_id`, `definition_snapshot`.

## Snapshot internals (source)

- `ConnectorData.AllBuildingConnectors[]` — primary IO model
- `ConnectorData.Tiles[]` — footprint tiles
- `CustomData` — often `$cycle` graph pointers (full sim config not flattened in analysis)

## Import / domain notes (source)

- Normalize to `building_variant`, `building_connector`, `building_footprint_tile` — **do not** duplicate 3.8 MB snapshots per group row
- `building_stable_id` always empty — parent FK backfill deferred (open in raw `08_risks_and_open_questions.md`)

## Open questions (source: raw `08_risks_and_open_questions.md`)

| Topic | Status |
|-------|--------|
| `CustomData` / 156 `$type` nodes | **unverified** — which nodes affect factory planner vs runtime-only |
| 34 `*Mirrored` variants | **unverified** — suffix pairing vs explicit `mirrored_from_id` FK |
| `building_stable_id` empty | **source** — parent FK backfill deferred at import |
| `LabelDefaultInternalVariant` (0 connectors) | **unverified** — special-case or incomplete dump |

## Cross-References

- [[building-definitions]]: 67 logical building groups
- [[building-groups]]: group membership references variants by internal name
- [[prefabs]]: visual prefab registry
- [[transport-system]]: belt/pipe layout variants share connector model
- [[deep-shallow-modules-ousterhout]]: avoid shallow per-`$type` tables without deep import boundary
