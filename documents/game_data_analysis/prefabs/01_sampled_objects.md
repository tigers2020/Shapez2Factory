# Random Sampling — `prefabs.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 763` |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(764), 3)` |
| Selected indices | **`65`**, **`415`**, **`463`** |

(Aligns with `asset_references.json` sample indices for cross-report traceability.)

---

## Sample A — index 65 (`ConstantSignal_Main_BakedMesh_Main_LOD0`)

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

**Interest:** Baked mesh + LOD0 variant — visual asset, not a simulation definition row.

---

## Sample B — index 415 (`Pipe_2UpLeft_PartialFluid_5`)

```json
{
  "stable_id": "fb6f7bdd367ffe03cc6ed8815fae36a548e511a71b878138776ec1cc7e77faa2",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "Pipe_2UpLeft_PartialFluid_5",
  "display_name_key": "Pipe_2UpLeft_PartialFluid_5",
  "prefab_path": "Pipe_2UpLeft_PartialFluid_5"
}
```

**Interest:** Pipe orientation + partial fluid naming — ties to transport/fluid presentation; may relate to `belts_pipes_transport.json` by name, not by `stable_id`.

---

## Sample C — index 463 (`Rotator_90CW_ArrowsBlueprint_Mesh_LOD2`)

```json
{
  "stable_id": "d30dc033d9717e16d109e90f6c24f4cbabd81bb27eaa1327b1b9f36dcd4d9829",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2",
  "display_name_key": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2",
  "prefab_path": "Rotator_90CW_ArrowsBlueprint_Mesh_LOD2"
}
```

**Interest:** Rotator blueprint mesh LOD2 — multiple LOD rows per building family are expected across the file.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| Unique `stable_id` | 764/764 |
| Empty `source_guid` | 764/764 |
| Flat envelope | No nested JSON |
| Meta registry coverage | 764 prefab `asset_references` links |
| LOD / BakedMesh heavy | 521 / 275 paths |

## Traceability

Each sample → one `prefab_asset` row + matching `asset_meta_reference` (prefab).
