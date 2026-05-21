# Domain Classification — `asset_references.json`

Classification applies to **fields** (and one implicit entity) discovered in the flat record schema. Full-file statistics drive enum-like fields; samples in `01_sampled_objects.md` illustrate prefab-heavy paths only.

## Entity-level inference

| Inferred entity | Classification | Rationale |
| --------------- | -------------- | --------- |
| Asset meta reference (one row per `.meta` capture) | **domain entity** | Answers “which Unity meta identity points at which canonical content asset?” |
| Prefab / sprite / material content asset | **domain entity (external)** | Defined in sibling JSON files; referenced via `ref_stable_id` |
| Root JSON array | **ordered child record container** | Import order may be preserved for audit; DB order is by `source_path` or PK |

---

## Field classification matrix

| JSON field | Classification | Notes |
| ---------- | -------------- | ----- |
| `stable_id` | **domain entity** (identifier) | Primary key for meta-reference row; not used in other game_data files |
| `ref_stable_id` | **relationship** | FK to content asset `stable_id` in prefabs/sprites/materials |
| `asset_type` | **enum / choice** | Closed set: `prefab`, `sprite`, `material` — selects FK target table |
| `source_path` | **entity attribute** | Logical Unity asset path; unique natural key |
| `display_name_key` | **entity attribute** | Intended localization key; in dump equals `source_path` |
| `source_guid` | **source metadata** (mislabeled) | Value is asset name string, not a GUID; **needs human review** for rename on import |
| `source_type_name` | **source metadata** | Constant `asset.meta` — dump capture channel, not gameplay type |
| *(implicit)* `prefab_path` / `sprite_path` / `material_path` | **entity attribute (external)** | Lives on sibling content records, not in this file |

---

## Fields absent from this file (related domain)

| Concept | Where observed | Classification |
| ------- | -------------- | -------------- |
| `prefab_path` | `prefabs.json` | entity attribute |
| `sprite_path` | `sprites.json` | entity attribute |
| `material_path` | `materials.json` | entity attribute |
| `UnityEngine.Object` | sibling `source_type_name` | **source metadata** |
| `Game.Content.*` types | other dumps (e.g. `manifest`, `raw_type_index`) | **runtime / reflection / debug metadata** — **not present here** |

---

## Runtime / reflection / debug metadata (special rule)

**None** of the following appear as values in `asset_references.json`:

```text
Game.Content.*
AtomicStatefulIslandSimulationSystem`2
Version=0.0.0.0
PublicKeyToken=null
#166
```

Closest risk items:

| Value | Actual classification | Domain use |
| ----- | --------------------- | ---------- |
| `source_type_name: "asset.meta"` | source metadata | Store on import audit / provenance column only |
| `source_guid: "<AssetName>"` | source metadata | Do **not** model as `GuidField`; map to `source_label` or denormalize from `source_path` |

---

## Unknown / needs human review

| Item | Question |
| ---- | -------- |
| `source_guid` semantics | Exporter naming suggests Unity GUID, but values are path strings. Confirm with dump tool authors. |
| `stable_id` hash algorithm | Assumed SHA-256 of canonical serialized identity; confirm reproducibility across re-dumps. |
| Why dual registry | Meta row and content row share `source_path` but differ in `stable_id`. Confirm whether planners need meta ID or only content ID. |
| `display_name_key` | Always equals path in v2 dump — verify if real localization keys arrive in future dumps. |
| Consumer references | No in-repo code references `asset_references` yet — downstream use (buildings? toolbar?) TBD. |

---

## Enum inventory

### `asset_type`

| Value | Count | Target content table |
| ----- | ----- | -------------------- |
| `prefab` | 764 | `prefab_asset` |
| `sprite` | 61 | `sprite_asset` |
| `material` | 4 | `material_asset` |

### `source_type_name`

| Value | Count |
| ----- | ----- |
| `asset.meta` | 829 |

Treat as **constant provenance**, not a user-facing enum.
