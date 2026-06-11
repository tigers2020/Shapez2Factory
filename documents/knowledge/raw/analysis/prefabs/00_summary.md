# File Inventory — `prefabs.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/prefabs.json` |
| File name | `prefabs.json` |
| File size | **224,810 bytes** |
| Manifest hash | `sha256:c73e364792d6cb2d80e00ec79a9e6234d06c5d16409bf3160a5ae2368018ee51` |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **764** |
| Element shape | **Flat object** (no `definition_snapshot`) |

## Per-element keys (764/764 identical schema)

| Key | Type | Distinct values |
| --- | ---- | ----------------- |
| `stable_id` | 64-char hex | **764** (all unique) |
| `source_type_name` | string | **1** (`UnityEngine.Object`) |
| `source_guid` | string | **1** (empty `""`) |
| `source_path` | string | **764** |
| `display_name_key` | string | **764** |
| `prefab_path` | string | **764** |

## Field equality (full file)

| Pair | Match rate |
| ---- | ---------- |
| `prefab_path == source_path` | 764/764 |
| `prefab_path == display_name_key` | 764/764 |

## Major object groups

| Group | Count | Notes |
| ----- | ----- | ----- |
| Prefab content records | 764 | Visual / mesh / transport prefab registry |
| Nested snapshots | 0 | Unlike `buildings.json` / `items.json` |

## Repeated structures

Single homogeneous envelope; no inner arrays or objects.

## Arrays detected

- Root array only

## Path naming patterns (inferred families)

| Prefix / pattern | Approx. count | Role |
| ---------------- | ------------- | ---- |
| `Wire*` | 140 | Wire transport visuals |
| `Pipe*` | 68 | Fluid pipe visuals |
| `LogicGate*` | 43 | Logic building meshes |
| `Lift*` | 31 | Lift variants |
| `*LOD*` in path | 521 | Level-of-detail mesh prefabs |
| `*BakedMesh*` | 275 | Baked mesh representations |

## Candidate IDs

| Field | Role |
| ----- | ---- |
| `stable_id` | **Canonical content ID** — unique; FK from `asset_references.ref_stable_id` |
| `prefab_path` | **Canonical logical name** — UNIQUE |
| `source_guid` | Not usable (empty) |
| `source_type_name` | Dump metadata only |

## Runtime / reflection / debug

- `UnityEngine.Object` on every row — **not** a domain entity name.

## Source metadata

- No transform hierarchy, components, or mesh GUIDs in JSON — **path + hash identity only**.

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `asset_references.json` | **764** `asset_type: prefab` rows; `ref_stable_id` resolves 764/764 |
| `building_variants.json` | **131** variants — weak string overlap with prefab paths (mesh LOD names differ) |
| `materials.json` / `sprites.json` | Sibling content registries |

## Design implication

764 rows → **`prefab_asset`** table (unique `stable_id`, `prefab_path`). Import before `asset_references.json`. Optional denormalized `path_family` from prefix parsing — not separate tables per prefab name.
