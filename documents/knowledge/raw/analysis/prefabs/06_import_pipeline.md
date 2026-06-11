# Import Pipeline — `prefabs.json`

**Prerequisites:** `manifest.json` → batch + `file_hashes.prefabs.json` verified.

**Order:** Import **`prefabs.json` before `asset_references.json`**.

## Stages (summary)

1. **Load** — UTF-8-SIG; verify SHA-256 `c73e364792d6cb2d80e00ec79a9e6234d06c5d16409bf3160a5ae2368018ee51`.
2. **Validate** — array length 764; required keys; unique `stable_id` and `prefab_path`.
3. **Normalize** — trim; NULL empty guid; optional `path_family` / LOD flags.
4. **Source metadata** — optional `source_object_record` per index.
5. **Sample evidence** — seed `20260521`, indices 65, 415, 463 in audit log.
6. **DTO** — `PrefabAssetDTO(stable_id, prefab_path, logical_path, display_name_key, flags…)`.
7. **Validate DTO** — 64-char hex ids; path non-empty.
8. **Upsert** — `prefab_asset` ON CONFLICT (`stable_id`).
9. **Children** — none.
10. **Resolve FK** — after `asset_references` import, 764 prefab meta rows must match.
11. **Invariants** — count 764; no orphan meta prefabs.
12. **Audit** — counts by `path_family`, LOD/baked totals, manifest hash.

## Idempotency

Natural keys: `stable_id`, `prefab_path`. Re-run yields identical 764 rows.

## Unknown fields → `unknown_property` only.
