# Random Sampling — `items.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 69` |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(70), 3)` |
| Selected indices | **`8`**, **`51`**, **`57`** |

## Sampled groups

| Index | `Hash` (abbrev) | `UniqueOperationId` | Structural interest |
| ----- | --------------- | ------------------- | ------------------- |
| 8 | `--------:CuWuSuRu` | 1017 | 2 layers; layer0 empty quadrants; layer1 filled |
| 51 | `P-P-P-P-:P-P-P-P-:P-P-P-P-:SuSuSuSu` | 1029 | 4 layers; pin-only layers + star layer |
| 57 | `CrCrCrCr` | 1320 | 1 layer; uniform red circles (primary color recipe) |

---

## Sample A — index 8

```json
{
  "definition_snapshot": {
    "Definition": {
      "UniqueOperationId": 1017,
      "PartCount": 4,
      "Hash": "--------:CuWuSuRu",
      "Layers": [
        { "Parts": [
          { "Shape": "", "Color": "" },
          { "Shape": "", "Color": "" },
          { "Shape": "", "Color": "" },
          { "Shape": "", "Color": "" }
        ]},
        { "Parts": [
          { "Shape": { "$unity": "MetaShapeSubPart", "name": "CircleQuad" }, "Color": { "name": "Uncolored" } },
          { "Shape": { "name": "DiamondQuad" }, "Color": { "name": "Uncolored" } },
          { "Shape": { "name": "StarQuad" }, "Color": { "name": "Uncolored" } },
          { "Shape": { "name": "RectQuad" }, "Color": { "name": "Uncolored" } }
        ]}
      ],
      "Id": { "Uid": 1017 }
    }
  }
}
```

**Pattern:** Top layer empty in data but encoded as `--------` in `Hash`; bottom layer `CuWuSuRu`.

---

## Sample B — index 51 (excerpt)

```json
{
  "UniqueOperationId": 1029,
  "Hash": "P-P-P-P-:P-P-P-P-:P-P-P-P-:SuSuSuSu",
  "Layers": [
    { "Parts": [ four PinQuad slots ] },
    { "Parts": [ four PinQuad slots ] },
    { "Parts": [ four PinQuad slots ] },
    { "Parts": [ four StarQuad + Uncolored color ] }
  ]
}
```

**Pattern:** Multi-layer pin stack ending in star shape layer; matches 4-segment hash.

---

## Sample C — index 57

```json
{
  "UniqueOperationId": 1320,
  "Hash": "CrCrCrCr",
  "Layers": [
    {
      "Parts": [
        { "Shape": { "name": "CircleQuad" }, "Color": { "name": "Red" } },
        { "Shape": { "name": "CircleQuad" }, "Color": { "name": "Red" } },
        { "Shape": { "name": "CircleQuad" }, "Color": { "name": "Red" } },
        { "Shape": { "name": "CircleQuad" }, "Color": { "name": "Red" } }
      ]
    }
  ]
}
```

**Pattern:** Single-layer monochromatic recipe; `Cr` = Circle + Red in hash alphabet.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| `PartCount == 4` | 70/70 |
| Empty `Shape` / `Color` | 296 / 527 empty color slots (partial recipes) |
| `Hash` unique | 70/70 |
| Layer count in hash (`:` + 1) | Matches `len(Layers)` |
| Subpart kinds | 8 (`PinQuad`, `CircleQuad`, `StarQuad`, `DiamondQuad`, `RectQuad`, converters, crystal) |

## Traceability

Samples map to `shape_recipe` + layers + `shape_quadrant_slot` rows.
