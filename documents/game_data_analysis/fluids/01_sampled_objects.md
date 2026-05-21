# Random Sampling — `fluids.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 8` (9 elements) |
| Sample size | **3** (file has ≥3 elements) |
| Method | `random.Random(20260521).sample(range(9), 3)` |
| Selected indices | **`1`**, **`3`**, **`6`** |

Because envelope fields are identical on every row, samples are distinguished by **palette color** only.

## Sampled groups

| Index | `Color.name` | Structural interest |
| ----- | ------------ | ------------------- |
| 1 | `Green` | Primary RGB source color; maps to solver code `g` in `COLOR_KINDS` |
| 3 | `Cyan` | Mixer-derived color in domain docs (`c`) |
| 6 | `Yellow` | Mixer-derived color (`y`) |

---

## Sample A — index 1 (`Green`)

```json
{
  "stable_id": "b1d8cb0cb37c27aa5076745b22500a16d395a6c3f2eab06424624d8ac839c648",
  "source_type_name": "ColorFluid",
  "source_guid": "ColorFluid",
  "source_path": "",
  "display_name_key": "ColorFluid",
  "definition_snapshot": {
    "Color": {
      "$unity": "MetaShapeColor",
      "name": "Green",
      "instance_id": 20044
    },
    "$type": "ColorFluid"
  }
}
```

---

## Sample B — index 3 (`Cyan`)

```json
{
  "definition_snapshot": {
    "Color": { "$unity": "MetaShapeColor", "name": "Cyan", "instance_id": 20048 },
    "$type": "ColorFluid"
  }
}
```

(Envelope fields omitted — identical to Sample A.)

---

## Sample C — index 6 (`Yellow`)

```json
{
  "definition_snapshot": {
    "Color": { "$unity": "MetaShapeColor", "name": "Yellow", "instance_id": 20052 },
    "$type": "ColorFluid"
  }
}
```

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| Duplicate `stable_id` | 9/9 rows share one hash |
| Unique `Color.name` | 9/9 distinct |
| `instance_id` sequential | 20042, 20044, … 20058 (step 2) |
| Monotonic dump order | Red → … → Uncolored (matches array index) |
| Aligns with `COLOR_KINDS` | 8 named colors + Uncolored (Black present in dump, separate from empty `-` code in catalog — **review**) |

## Traceability

Each sample maps to `fluid_color.color_name` + `source_row_index` (see `03_reconstructed_schema.md`).
