# Random Sampling — `shapes.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | `0 .. 1169` |
| Sample size | **3** |
| Selected indices | **`131`**, **`831`**, **`927`** |

```python
random.Random(20260521).sample(range(1170), 3)  # [131, 831, 927]
```

---

## Sample A — index 131 (3-layer crystal / white)

```json
{
  "display_name_key": "#132",
  "source_type_name": "ShapeDefinition",
  "definition_snapshot": {
    "UniqueOperationId": 132,
    "PartCount": 4,
    "Hash": "cwRwcwcw:cwCwcwcw:cccccccc",
    "Layers": [ "…3 layers, CrystalQuad + White …" ],
    "Id": { "Uid": 132 }
  }
}
```

**Interest:** Multi-layer hash with `:` segments; crystal subpart + colored layers.

---

## Sample B — index 831 (single-layer)

```json
{
  "UniqueOperationId": 832,
  "Hash": "CwXrCwWr",
  "PartCount": 4,
  "Layers": [ { "Parts": [ { "Shape": { "name": "CircleQuad" }, "Color": { "name": "White" } } ] } ]
}
```

**Interest:** Single-layer compact hash; typical CircleQuad + paint pattern.

---

## Sample C — index 927

```json
{
  "UniqueOperationId": 928,
  "Hash": "RuCuCuCu",
  "Layers": [ { "Parts": [ { "Shape": { "name": "RectQuad" }, "Color": { "name": "Uncolored" } } ] } ]
}
```

**Interest:** Monochrome rect shape code (`Ru` tokens); uncolored base.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| `Hash` unique | 1170/1170 |
| `UniqueOperationId` unique | 1170/1170 |
| `items.json` ⊆ shapes | 70/70 hashes |
| Research costs ⊆ shapes | 253/253 ShapeHash |
| `PartCount == 4` | 1170/1170 |
| Empty Shape/Color slots | thousands of `""` quadrants |

## Traceability

Samples → `shape_recipe` + layers + quadrant slots (same schema as `items` analysis).
