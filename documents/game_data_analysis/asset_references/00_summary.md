# File Inventory — `asset_references.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/asset_references.json` |
| File name | `asset_references.json` |
| Manifest hash | `sha256:19ef2e3e72f158996a1b128ee6c3916df2b2c4a228499771c279c76db766dcc5` (from `manifest.json`) |
| Approx. size | 307,096 bytes |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, `dump_schema_version: 1.0.0` |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **829** |
| Element type | **object** (100% homogeneous) |
| Nesting depth | **1** (flat records only; no nested objects or child arrays) |

There are **no top-level keys** (root is not an object). The file is a single homogeneous list, not a keyed map.

## Major object groups

Because every element shares the same schema, “groups” are **logical partitions**, not structural JSON branches:

| Group | Count | Partition key | Notes |
| ----- | ----- | ------------- | ----- |
| Prefab meta references | 764 | `asset_type == "prefab"` | LOD meshes, baked meshes, pipe partials, blueprint meshes |
| Sprite meta references | 61 | `asset_type == "sprite"` | UI/toolbar icon assets |
| Material meta references | 4 | `asset_type == "material"` | Shader/material assets |
| **Total** | **829** | | Matches `prefabs.json` (764) + `sprites.json` (61) + `materials.json` (4) |

## Per-record field inventory (829/829 presence)

| Field | JSON type | Distinct values | Role (initial) |
| ----- | --------- | --------------- | -------------- |
| `stable_id` | string (64 hex) | 829 unique | Meta-side canonical identity |
| `ref_stable_id` | string (64 hex) | 829 unique | FK to content asset in sibling dumps |
| `asset_type` | string | 3 (`prefab`, `sprite`, `material`) | Polymorphic discriminator |
| `source_path` | string | 829 unique | Unity asset logical path / name |
| `source_guid` | string | 829 unique | **Misnamed**: equals `source_path`, not a UUID |
| `display_name_key` | string | 829 unique | Localization/display key (here identical to path) |
| `source_type_name` | string | 1 (`asset.meta`) | Dump provenance label |

## Repeated structures

- **One schema** repeated 829 times (7 scalar fields).
- No repeated nested object templates.
- No ordered child arrays inside records.

## Arrays detected

- Root: `[]` array of 829 objects only.
- No arrays inside elements.

## Nested objects

- **None** at any depth.

## Candidate IDs

| Field | Format | Uniqueness | Recommended role |
| ----- | ------ | ----------- | ---------------- |
| `stable_id` | 64-char lowercase hex (SHA-256-like) | Unique in file | Primary key for **meta reference** row |
| `ref_stable_id` | Same format | Unique in file; **0** appear as another row’s `stable_id` | FK to **content asset** (`prefabs` / `sprites` / `materials`) |
| `source_path` | PascalCase asset name string | Unique in file | Natural key / lookup path (not hash) |
| `source_guid` | Same as `source_path` in all 829 rows | Unique | **Not a GUID** — treat as duplicate path label |
| `display_name_key` | Same as `source_path` in all 829 rows | Unique | i18n key candidate |

## Runtime / reflection / debug strings

- **No** `Game.Content.*`, assembly qualified type names, `Version=`, or `#166` style strings in this file.
- `source_type_name: "asset.meta"` is **dump provenance** (how the row was captured), not a domain entity name.
- Field name `source_guid` is **misleading metadata** from the exporter; values are asset path strings.

## Possible source metadata

| Signal | Classification |
| ------ | -------------- |
| `source_type_name` | Source metadata (always `asset.meta`) |
| `source_path`, `source_guid` | Observed asset labels from Unity export |
| `manifest.json` dump headers | External provenance for entire `game_data/` bundle |
| Sibling files `prefabs.json`, `sprites.json`, `materials.json` | Canonical content targets for `ref_stable_id` |

## Cross-file structural relationship (inventory-level)

Verified on full corpus:

- Every `ref_stable_id` resolves to exactly one `stable_id` in:
  - `prefabs.json` (764/764 prefab rows)
  - `sprites.json` (61/61 sprite rows)
  - `materials.json` (4/4 material rows)
- **829/829** rows resolve; **0** orphan `ref_stable_id` within the game_data bundle.
- For prefab rows, `source_path` in `asset_references` **equals** `source_path` in the linked prefab record (764/764).
- `asset_references.stable_id` does **not** appear in other game_data JSON files (meta-only identity).

## Implications for DB design

- Do **not** mirror the JSON array as a generic `payload` table.
- Model as a narrow **meta-reference bridge** table plus separate content tables imported from sibling files.
- Import **content assets first**, then meta references (FK dependency).
