# Import Pipeline Plan — `asset_references.json`

Deterministic, idempotent import into normalized tables. **Prerequisite:** `prefabs.json`, `sprites.json`, `materials.json` imported first (FK targets).

---

## Stage overview

```text
1. Load JSON
2. Validate structure
3. Normalize keys and scalar values
4. Register source object metadata
5. Randomly sample 2–3 groups for report evidence
6. Extract canonical DTOs
7. Validate DTOs
8. Upsert root entities by canonical ID
9. Upsert child entities by parent canonical ID + order/index/key
10. Resolve FK and M2M references
11. Validate invariants
12. Write import audit summary
```

---

## Stage 1 — Load JSON

- Read `documents/game_data/asset_references.json` as UTF-8.
- Parse to `list[dict]`.
- Load `manifest.json` (UTF-8-sig) for `file_hashes["asset_references.json"]`.

**Exit criteria:** JSON parses; root is `list`; length == 829 (or manifest-expected count if versioned).

---

## Stage 2 — Validate structure

| Rule | Action on failure |
| ---- | ----------------- |
| Each element is `dict` | Hard fail |
| Required keys exactly: 7 fields | Hard fail |
| No extra keys | Route to `UnknownProperty` (soft capture) |
| `stable_id`, `ref_stable_id` match `^[a-f0-9]{64}$` | Hard fail |
| `asset_type` in allowed enum | Hard fail |
| `source_type_name == "asset.meta"` | Warn if different (schema drift) |

---

## Stage 3 — Normalize keys and scalar values

- Lowercase hex IDs (already lowercase).
- Strip whitespace on strings (none expected).
- Map JSON `asset_type` → DTO `AssetKind` enum.
- Rename DTO field: `source_guid` → `source_label` (avoid GUID confusion).
- Set `source_row_index` from enumerate order.

**Do not** normalize away path casing — paths are case-sensitive asset names.

---

## Stage 4 — Register source object metadata

Insert/update `game_data_import_batch`:

- `file_hash` from manifest
- `dump_schema_version`, `dump_timestamp_utc`, `source_method`
- `record_count_asset_meta = 829`

Store per-row `dump_source_type` from `source_type_name`.

---

## Stage 5 — Random sample for report evidence

- Use fixed seed `20260521` (documented in `01_sampled_objects.md`).
- Sample 3 indices; log in import audit (not used for business logic).
- **Import does not depend on sample randomness.**

---

## Stage 6 — Extract canonical DTOs

```python
@dataclass(frozen=True)
class AssetMetaReferenceDTO:
    meta_stable_id: str
    content_stable_id: str
    asset_kind: AssetKind  # PREFAB | SPRITE | MATERIAL
    logical_path: str
    display_name_key: str
    source_label: str | None
    dump_source_type: str
    source_row_index: int
```

Sibling DTOs (`PrefabAssetDTO`, etc.) come from other files in same pipeline run.

---

## Stage 7 — Validate DTOs

- `meta_stable_id != content_stable_id`
- `logical_path` non-empty
- `display_name_key` non-empty
- `asset_kind` consistent with target table membership (pre-check against loaded content ID sets)

---

## Stage 8 — Upsert root entities by canonical ID

**Order:**

1. `prefab_asset` upsert on `stable_id` (from `prefabs.json`)
2. `sprite_asset` upsert on `stable_id`
3. `material_asset` upsert on `stable_id`
4. `asset_meta_reference` upsert on `meta_stable_id`

Upsert key: natural hash IDs, not array index.

---

## Stage 9 — Upsert child entities

Not applicable — flat rows only. `source_row_index` stored as ordering metadata under import batch (ordered child audit).

---

## Stage 10 — Resolve FK and M2M references

For each `AssetMetaReferenceDTO`:

```text
if asset_kind == PREFAB:
    assert content_stable_id in prefab_asset.stable_id set
elif asset_kind == SPRITE:
    assert content_stable_id in sprite_asset.stable_id set
elif asset_kind == MATERIAL:
    assert content_stable_id in material_asset.stable_id set
```

Optional denormalized check: `logical_path` == content row `logical_path`.

**No M2M** resolution required.

---

## Stage 11 — Validate invariants

| Invariant | Check |
| --------- | ----- |
| Row count | `asset_meta_reference` count == 829 |
| Unique meta IDs | `meta_stable_id` unique |
| Unique paths | `logical_path` unique |
| No orphan FK | all `content_stable_id` exist in content tables |
| 1:1 meta↔content | each `content_stable_id` referenced exactly once |
| Enum validity | `asset_kind` only three values |
| No domain JSONField blobs | domain tables have scalar columns only |
| Runtime names excluded | no column named `asset_meta` or `UnityEngine_Object` |

---

## Stage 12 — Write import audit summary

Emit structured summary:

```json
{
  "file": "asset_references.json",
  "batch_id": "...",
  "rows_upserted": 829,
  "prefab_links": 764,
  "sprite_links": 61,
  "material_links": 4,
  "orphan_ref_stable_id": 0,
  "unknown_properties": 0,
  "checksum": "sha256:..."
}
```

Store audit row linked to `game_data_import_batch`.

---

## Idempotency rules

| Rule | Implementation |
| ---- | -------------- |
| Same input → same rows | Upsert on natural keys (`meta_stable_id`, content `stable_id`) |
| Same relationships | FK columns overwritten identically |
| Same ordering | `source_row_index` from array position |
| Same checksum | Canonical JSON serialization per row (sorted keys) hashed |
| Re-import | Updates scalars; does not duplicate rows |

**Unknown fields:** insert into `unknown_property`, never merge into domain columns silently.

**Runtime/debug metadata:** `dump_source_type`, `source_method` → batch/audit tables only.

---

## Suggested Django management command layout

```text
game_data_import
  ├─ import_content_assets (prefabs, sprites, materials)
  └─ import_asset_meta_references (depends on content)
```

Single transaction per batch recommended with `DEFERRABLE` FK checks after content load.
