# Risks and Open Questions — `buildings.json`

## Uncertain fields

| Item | Risk |
| ---- | ---- |
| Duplicate 13 MB file vs `building_groups.json` | Storage/import drift if both write snapshot |
| `$cycle` Definitions (34) | Resolver correctness |
| `Title`/`Description` `$cycle` inside snapshot | i18n resolution |
| `StructureOverview` | Planner vs wiki-only |
| `RequiredStoreContentId` | No store schema |

## Human review

| Question |
| -------- |
| Is `buildings.json` or `building_groups.json` the UI display authority? |
| Should `building` and `building_group_registry` be one table with two hash columns? |
| Import embedded variant geometry or always trust `building_variants.json`? |

## Runtime metadata risks

- `BuildingDefinitionGroup` as model name
- 152 `$type` → 152 tables anti-pattern
- 5,564 backing-field keys
- Unity `instance_id` as FK

## Ambiguous IDs

- `stable_id` (buildings) vs `stable_id` (groups) — parallel namespaces
- `display_name_key` plain vs LazyText in sibling file

## Version drift

- Count 67, hash in manifest
- Game version `unknown+1.0.3-rc3`

## Missing targets

- `translations.json` incomplete
- `simulation_systems` does not reference `source_guid` directly
- No Django importer in repo yet

## Defer tables

- `buildings_raw`
- Per-`$type` requirement classes as ORM models
- Full `structure_overview` relational model

## Duplication risk (critical)

67 identical snapshots also in `building_groups.json` — **single canonical import path** for snapshot-derived columns.

## Risk summary

| Area | Level |
| ---- | ----- |
| Envelope | Low |
| Snapshot | Very high (13 MB) |
| FK to variants | Low (97+34) |
| i18n | High (split across files) |
| Planner | Medium (toolbar/research textual) |
