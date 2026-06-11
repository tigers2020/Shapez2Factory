# File Inventory — `sprites.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/sprites.json` |
| File name | `sprites.json` |
| File size | **14,943 bytes** |
| Manifest hash | `sha256:802f9fb6facfdeb37cb040549a12939cf222dd60dda0e4fe7121e459bcb68852` |
| Dump context | `manifest.json` → `runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **61** |
| Element shape | **Flat object** (no `definition_snapshot`) |

## Per-element keys (61/61)

| Key | Type | Distinct values |
| --- | ---- | ----------------- |
| `stable_id` | 64-char hex | **61** (unique) |
| `sprite_path` | string | **61** |
| `source_path` | string | **61** (equals `sprite_path`) |
| `display_name_key` | string | **61** (equals `sprite_path`) |
| `source_type_name` | string | **1** (`UnityEngine.Object`) |
| `source_guid` | string | **1** (empty `""`) |

## Major object groups

| Group | Count | Role |
| ----- | ----- | ---- |
| Sprite / icon content records | 61 | UI & building icon registry |
| Nested snapshots | 0 | Path identity only (like `materials.json`) |

## Repeated structures

Single homogeneous envelope; no inner arrays or objects.

## Naming patterns (inferred)

| Pattern | Examples |
| ------- | -------- |
| `*Icon` suffix | `BeltReaderIcon`, `LogicGateOrIcon`, `ButtonIcon` |
| `LogicGate*` prefix | compare/or/and variants |
| `Belt*` transport UI | belt, port, filter icons |

## Candidate IDs

| Field | Role |
| ----- | ---- |
| `stable_id` | **Canonical content ID** — unique; FK from `asset_references.ref_stable_id` |
| `sprite_path` | **Canonical logical name** — UNIQUE |
| `source_guid` | Not usable (empty) |
| `source_type_name` | Dump metadata only |

## Runtime / reflection / debug

- `UnityEngine.Object` on every row — not a domain entity name.

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `asset_references.json` | **61** `asset_type: sprite` rows; **61/61** `ref_stable_id` resolve |
| `prefabs.json` / `materials.json` | Sibling content registries (764 / 4 rows) |
| `building_variants.json` | Inferred UI icons for buildings/logic (by path name, no JSON FK) |
| `translations.json` | Empty — no localized labels |

## Design implication

**61** rows → **`sprite_asset`** table (`stable_id`, `sprite_path`). Import **before** `asset_references.json`. No `sprites_raw_json`, no `UnityEngineObject` model.
