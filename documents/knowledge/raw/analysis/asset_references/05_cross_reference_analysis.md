# Cross-Reference Analysis — `asset_references.json`

## Relationship summary

`asset_references.json` is a **bridge layer** between Unity `.meta` capture identities and canonical **content assets** exported separately. It does not introduce buildings, recipes, or simulation systems directly.

---

## FK relationships (resolved)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `asset_meta_reference.content_stable_id` | `prefab_asset.stable_id` | 764 : 1 | `asset_type=prefab`; full hash match |
| `asset_meta_reference.content_stable_id` | `sprite_asset.stable_id` | 61 : 1 | `asset_type=sprite` |
| `asset_meta_reference.content_stable_id` | `material_asset.stable_id` | 4 : 1 | `asset_type=material` |
| `asset_meta_reference.import_batch_id` | `game_data_import_batch.id` | N : 1 | inferred from manifest |

**Total resolved FKs:** 829/829 (100%).

---

## FK relationships (internal to this file)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `asset_meta_reference.meta_stable_id` | `asset_meta_reference.ref_stable_id` | — | **Never equal** (0 rows) |
| `asset_meta_reference.meta_stable_id` | another row’s `meta_stable_id` via `ref_stable_id` | — | **0** — `ref_stable_id` never appears as any row’s `stable_id` |

Interpretation: **two parallel stable ID namespaces** — meta vs content — for the same logical path.

---

## M2M relationships

**None** in this file. Each meta reference points to exactly one content asset; no join tables or arrays.

---

## Ordered child relationships

| Parent | Child | Order key |
| ------ | ----- | --------- |
| `game_data_import_batch` | `asset_meta_reference` rows | `source_row_index` (= JSON array index) |

Import should preserve array order in `source_row_index` for reproducible checksums even if logical sort differs.

---

## Inferred references by ID (outbound)

| ID field | Resolves in | Unresolved count |
| -------- | ----------- | ---------------- |
| `ref_stable_id` | `prefabs.json`, `sprites.json`, `materials.json` | **0** |
| `stable_id` (meta) | *no other game_data JSON* | N/A (leaf identity) |

---

## Inferred references by path (secondary)

| Path field | Matches | Notes |
| ---------- | ------- | ----- |
| `source_path` | sibling content `source_path` | 829/829 same string pairs for linked rows |
| `display_name_key` | `source_path` | No extra translation table in bundle |

---

## Unresolved references

| Reference type | Status |
| -------------- | ------ |
| `ref_stable_id` → content tables | **Resolved** |
| `stable_id` → buildings / variants / toolbar | **Not observed** in current `game_data/` — may appear in future dumps or code |
| Meta `stable_id` in runtime code | **Unknown** — no repo usages found |

---

## Source metadata references

| Field | Points to | Domain impact |
| ----- | --------- | ------------- |
| `source_type_name: asset.meta` | Dump pipeline channel | Audit only |
| Sibling `source_type_name: UnityEngine.Object` | Content capture channel | On content tables, not meta table |
| `manifest.source_method: runtime_reflection` | Whole bundle | Import batch metadata |

---

## Unknown references needing review

1. Whether **gameplay systems** (buildings, toolbar) will reference `meta_stable_id` or only `content_stable_id`.
2. Whether `asset_references.json` is **redundant** for planners if content tables are authoritative (could be audit-only ingestion).
3. Cross-bundle references outside `documents/game_data/` (mods, DLC) — not in sample.

---

## Relationship diagram

```text
game_data_import_batch
  └─ has many → asset_meta_reference (829)
        ├─ asset_kind=prefab ──► prefab_asset (764)
        ├─ asset_kind=sprite ──► sprite_asset (61)
        └─ asset_kind=material ──► material_asset (4)

prefab_asset
  └─ referenced by → asset_meta_reference (meta stable_id ≠ content stable_id)
       └─ same logical_path (denormalized string match)

sprite_asset
  └─ referenced by → asset_meta_reference (icons)

material_asset
  └─ referenced by → asset_meta_reference (shaders/materials)

buildings.json / building_variants.json
  └─ (no direct stable_id overlap with asset_references in current dump)
       └─ future link likely via paths or separate FK dump — needs review
```

---

## Cardinality proof (full file)

| Metric | Value |
| ------ | ----- |
| Rows | 829 |
| Distinct `meta_stable_id` | 829 |
| Distinct `ref_stable_id` | 829 |
| Distinct `source_path` | 829 |
| Content targets (prefab+sprite+material) | 829 |
| Orphan `ref_stable_id` | 0 |

Each content asset appears referenced by **exactly one** meta reference (1:1 meta↔content pairing across bundle).
