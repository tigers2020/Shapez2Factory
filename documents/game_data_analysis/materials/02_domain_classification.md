# Domain Classification — `materials.json`

## Legend

| Tag | Meaning |
| --- | ------- |
| domain entity | Planner/rendering asset |
| entity attribute | Scalar field |
| relationship | FK to another table |
| ordered child record | Ordered array child |
| enum / choice | Closed set |
| source metadata | Dump provenance |
| runtime / reflection / debug metadata | Not domain keys |
| unknown / needs human review | Ambiguous |

---

## Per-element fields

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `[i]` | domain entity | → `material_asset` |
| `[i].stable_id` | entity attribute | **Unique** content hash |
| `[i].material_path` | entity attribute | Canonical resource name |
| `[i].source_path` | entity attribute | Redundant with `material_path` here |
| `[i].display_name_key` | entity attribute | i18n key; translations dump empty |
| `[i].source_type_name` | source metadata | `UnityEngine.Object` |
| `[i].source_guid` | source metadata | Empty string |
| (missing shader/properties) | unknown / needs human review | Not in reflection export |

---

## Rejected as domain entities

| Label | Reason |
| ----- | ------ |
| `UnityEngine.Object` | `source_type_name` only |
| `Material` (C# type) | Not present in JSON |
| Table per array index | Anti-pattern |

---

## Inferred domain entities

| Entity | Evidence |
| ------ | -------- |
| **Material asset** | 4 unique materials; referenced by meta registry |
| **Import batch** | From `manifest.json` (external) |

---

## Enum / choice (inferred)

| Set | Values |
| --- | ------ |
| Material logical names | 4 fixed paths in this dump |
| Future materials | Open set — validate on import |

---

## Human review

| Item | Question |
| ---- | -------- |
| Shader / texture data | Capture in future dump or resolve via Unity asset pipeline? |
| `PainterRoll` vs `PainterRollMinimal` | When is each used in buildings? |
