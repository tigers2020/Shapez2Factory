# File Inventory — `raw_type_index.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/raw_type_index.json` |
| File name | `raw_type_index.json` |
| File size | **~1,852,587 bytes** |
| Manifest hash | `sha256:1af48c8f13164cd693f90b8279a05b165a1cd3af09643a8e1029a085fe04ffd8` |
| Dump context | `manifest.json` → `source_method: runtime_reflection` |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **6,497** |
| Element shape | **Flat object** (7 keys, no nesting) |

## Per-element keys (6,497/6,497)

| Key | Type | Distinct values | Notes |
| --- | ---- | ----------------- | ----- |
| `stable_id` | 64-char hex | **6,383** | **Not unique** (114 extra rows) |
| `type_name` | string | **6,383** | Short CLR type name |
| `assembly_name` | string | **37** | Logical assembly bucket |
| `source_type_name` | string | **6,497** | **Always equals `type_name`** |
| `source_path` | string | **1** (`""`) | Empty on all rows |
| `source_guid` | string | **1** (`""`) | Empty |
| `display_name_key` | string | **1** (`""`) | Empty |

## Major object groups

| Group | Count | Role |
| ----- | ----- | ---- |
| CLR type registry entries | 6,497 | Reflection catalog |
| Unique `(type_name, assembly_name)` | **6,497** | **True canonical composite key** |
| Duplicate `stable_id` clusters | 8 ids × many assemblies | Hash collision / generator artifact |

## Repeated structures

Homogeneous flat row; no nested objects or child arrays.

## Arrays detected

- Root array only

## Assembly distribution (top)

| `assembly_name` | Rows |
| --------------- | ---- |
| `SPZGameAssembly` | 3,306 |
| `Game.Content` | 593 |
| `Game.Content.Features` | 454 |
| `ShapezShifter` | 394 |
| `Game.Orchestration` | 296 |
| … | 32 more assemblies |

## Candidate IDs

| Field | Role |
| ----- | ---- |
| `(type_name, assembly_name)` | **Canonical business key** (UNIQUE 6,497/6,497) |
| `type_name` alone | **Not unique** across assemblies |
| `stable_id` | **Not unique** — audit only; do not use as sole PK |
| `assembly_name` | FK-ish link to `manifest.assembly_hashes` (name without `.dll`) |

## Runtime / reflection / debug strings

| Pattern | Count (approx.) | Examples |
| ------- | --------------- | -------- |
| Compiler-generated types | ~1,892 | `HUDDebugStats+<>c__DisplayClass5_0`, `<PrivateImplementationDetails>` |
| `UnitySourceGeneratedAssemblyMonoScriptTypes_v1` | 35 rows / 8 `stable_id` dupes | Same type name, different `assembly_name` |
| `Game.*` prefix in `type_name` | 1,308 | Content/orchestration types |
| `*Simulation*` in name or assembly | ~847 | Simulation stack types |

**Must not** become Django model class names (`ShapeOperationPaintPayload`, etc.).

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `manifest.json` | `assembly_hashes` keys align with `assembly_name` + `.dll` |
| `items.json`, `buildings.json`, … | `source_type_name` strings may appear as `type_name` here |
| `asset_references.json` | **No** direct stable_id link (separate content registry) |
| `prefabs.json` | Uses `UnityEngine.Object`, not indexed by type row |

## Design implication

Normalize to **`clr_type_registry_entry`** (or `game_data_type_catalog_entry`) with UNIQUE (`type_name`, `assembly_name`). Store non-unique `stable_id` as audit hash only. **Audit / lookup table**, not gameplay simulation tables. No `raw_type_index_json` dump table.
