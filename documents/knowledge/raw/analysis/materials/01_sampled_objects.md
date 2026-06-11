# Random Sampling — `materials.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 3` (4 elements) |
| Sample size | **3** (file has ≥3 groups) |
| Method | `random.Random(20260521).sample(range(4), 3)` |
| Selected indices | **`0`**, **`1`**, **`2`** |

---

## Sample A — index 0 (`LabelTextMaterial`)

```json
{
  "stable_id": "a77f995fe9e6384f46202df254bd3bc9bbdae23d7bf5c56acdc15e3640546f70",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "LabelTextMaterial",
  "display_name_key": "LabelTextMaterial",
  "material_path": "LabelTextMaterial"
}
```

**Interest:** UI/label material; baseline envelope where all path fields align.

---

## Sample B — index 1 (`MixerFluidMaterial`)

```json
{
  "stable_id": "7074a3f1e92ec803438acbde9eb81aaa41784497e7ef6dffeb3248144e0dfaaa",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "MixerFluidMaterial",
  "display_name_key": "MixerFluidMaterial",
  "material_path": "MixerFluidMaterial"
}
```

**Interest:** Links fluid/mixer presentation to `fluids.json` palette indirectly (no FK in JSON).

---

## Sample C — index 2 (`PainterRollMaterial`)

```json
{
  "stable_id": "b590adedb2a4bc2e7795c9a0d909aee9c23443a305db8db355ddb2850726a2a8",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "PainterRollMaterial",
  "display_name_key": "PainterRollMaterial",
  "material_path": "PainterRollMaterial"
}
```

**Interest:** Painter variant pair with index 3 (`PainterRollMinimalMaterial`) — two stable IDs for related buildings.

---

## Not sampled (index 3)

`PainterRollMinimalMaterial` — structurally identical envelope; documents minimal painter material sibling.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| `material_path == source_path == display_name_key` | 4/4 |
| Unique `stable_id` | 4/4 |
| Empty `source_guid` | 4/4 |
| No nested definition | 4/4 flat |
| 1:1 `asset_references` material rows | 4 meta refs by `ref_stable_id` |

## Traceability

Samples map 1:1 to `material_asset` rows and `asset_meta_reference` (material kind) children.
