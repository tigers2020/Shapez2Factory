# Random Sampling — `asset_references.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Array indices `0 .. 828` (829 elements) |
| Sample size | **3** (file has ≥3 elements) |
| Selection method | `random.Random(20260521).sample(range(829), 3)` → sorted for readability |
| Selected indices | **`65`**, **`415`**, **`463`** |

Sampling is over **array elements**, not hand-picked “interesting” buildings. Post-selection notes explain structural interest only for documentation.

## Why these samples are structurally useful

| Index | `asset_type` | Structural interest |
| ----- | ------------ | ------------------- |
| 65 | `prefab` | Typical **BakedMesh + LOD0** naming; shows meta↔prefab dual-`stable_id` pattern |
| 415 | `prefab` | **Pipe partial fluid** variant (`PartialFluid` in path) — transport subdomain asset |
| 463 | `prefab` | **Blueprint mesh LOD2** — multi-LOD / blueprint representation family |

All three are prefab-meta rows (764/829). Sprite and material groups are not in this sample draw but are fully classified in `02_domain_classification.md` from full-file stats.

---

## Sample A — index 65

```json
{
  "stable_id": "df4ee2afafd32ff6a31f84a88301fa35f1f1cc9729ed36ee72e4dad6d222b2aa",
  "source_type_name": "asset.meta",
  "source_guid": "ConstantSignal_Main_BakedMesh_Main_LOD0",
  "source_path": "ConstantSignal_Main_BakedMesh_Main_LOD0",
  "display_name_key": "ConstantSignal_Main_BakedMesh_Main_LOD0",
  "asset_type": "prefab",
  "ref_stable_id": "0dae242b6a0c659b6693ce1c50e0c505e3402eb43985bc63091bbdb6b3ddc715"
}
```

**Linked prefab** (`prefabs.json`, `stable_id == ref_stable_id`):

```json
{
  "stable_id": "0dae242b6a0c659b6693ce1c50e0c505e3402eb43985bc63091bbdb6b3ddc715",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "ConstantSignal_Main_BakedMesh_Main_LOD0",
  "display_name_key": "ConstantSignal_Main_BakedMesh_Main_LOD0",
  "prefab_path": "ConstantSignal_Main_BakedMesh_Main_LOD0"
}
```

**Pattern:** same `source_path`, different `stable_id`, different `source_type_name` (`asset.meta` vs `UnityEngine.Object`).

---

## Sample B — index 415

```json
{
  "stable_id": "5187830ae1e6d9cf2c3a000676eea27197e169f8ee7ec83813e1f31d8826e377",
  "source_type_name": "asset.meta",
  "source_guid": "Pipe_2UpLeft_PartialFluid_5",
  "source_path": "Pipe_2UpLeft_PartialFluid_5",
  "display_name_key": "Pipe_2UpLeft_PartialFluid_5",
  "asset_type": "prefab",
  "ref_stable_id": "fb6f7bdd367ffe03cc6ed8815fae36a548e511a71b878138776ec1cc7e77faa2"
}
```

**Pattern:** pipe/fluid visual slice asset; confirms transport-related paths appear in meta registry same as prefab registry.

---

## Sample C — index 463

```json
{
  "stable_id": "d060181c8d2de6d3edbb7ce9de86bf6bd6a2f9badefa870a7c50b6b59fc28a13",
  "source_type_name": "asset.meta",
  "source_guid": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2",
  "source_path": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2",
  "display_name_key": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2",
  "asset_type": "prefab",
  "ref_stable_id": "d30dc033d9717e16d109e90f6c24f4cbabd81bb27eaa1327b1b9f36dcd4d9829"
}
```

**Pattern:** blueprint mesh with explicit `LOD2` suffix — supports treating path suffixes as variant dimensions, not separate domain entities.

---

## Full-file patterns informed by samples (not only samples)

| Pattern | Count | Notes |
| ------- | ----- | ----- |
| `_LOD` in `source_path` | 521 | Level-of-detail assets |
| `BakedMesh` in path | 275 | Baked mesh representations |
| `Blueprint` in path | 80 | Blueprint-derived meshes |
| `PartialFluid` in path | 50 | Partial fluid pipe visuals |
| `ref_stable_id == stable_id` | 0 | Always distinct IDs |
| `display_name_key == source_path` | 829 | No separate i18n indirection in this dump |

## Traceability

Each sampled object maps to proposed table `asset_meta_reference` (see `03_reconstructed_schema.md`) with FK `content_stable_id →` `prefab_asset` | `sprite_asset` | `material_asset` based on `asset_type`.
