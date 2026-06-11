# Domain Classification — `items.json`

## Classification legend

| Tag | Meaning |
| --- | ------- |
| **domain entity** | First-class game/planner concept |
| **entity attribute** | Scalar property of an entity |
| **relationship** | FK / composition |
| **ordered child record** | Ordered array → child table |
| **enum / choice** | Closed set |
| **source metadata** | Dump/provenance |
| **runtime / reflection / debug metadata** | Not domain keys |
| **unknown / needs human review** | Ambiguous |

---

## Envelope

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `stable_id` | source metadata | **Non-unique**; audit only |
| `source_guid` | source metadata | Constant `ShapeItem` |
| `source_type_name` | source metadata | |
| `display_name_key` | source metadata | |
| `source_path` | source metadata | Empty |
| `definition_snapshot` | source metadata | Wrapper |

---

## Definition root

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `Definition.UniqueOperationId` | **entity attribute** | Canonical numeric id |
| `Definition.PartCount` | **entity attribute** | Always 4 |
| `Definition.Hash` | **entity attribute** | **Canonical shape code** |
| `Definition.Id.Uid` | **entity attribute** | Duplicate of operation id |
| `Definition.$type` | source metadata | |
| `Definition.Layers` | **ordered child record** | → `shape_recipe_layer` |

---

## Layers and parts

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `Layers[i]` | **ordered child record** | `layer_index = i` |
| `Layers[i].Parts[j]` | **ordered child record** | `quadrant_index = j` (0–3) |
| `Parts[j].Shape` | **relationship** | → `shape_component_kind` |
| `Parts[j].Shape.name` | **enum / choice** | Subpart kind |
| `Parts[j].Shape.$unity` | source metadata | |
| `Parts[j].Shape.instance_id` | runtime / reflection / debug metadata | |
| `Parts[j].Color` | **relationship** | → `fluid_color` |
| `Parts[j].Color.name` | **enum / choice** | 9 palette names |
| `Parts[j].Color.instance_id` | runtime / reflection / debug metadata | |
| `Parts[j].Shape == ""` | **entity attribute** | Empty quadrant |
| `Parts[j].Color == ""` | **entity attribute** | Empty color slot |

---

## Hash encoding (inferred)

| Observation | Classification | Notes |
| ----------- | -------------- | ----- |
| `Hash` segments split by `:` | **entity attribute** | One segment per layer |
| Tokens like `Cu`, `Ru`, `P-`, `Cr` | **unknown / needs human review** | Two-char shape+color code; align with `COLOR_KINDS` / `SHAPE_KINDS` |
| `Ck` (Black) | **unknown / needs human review** | Letter `k` not in `COLOR_KINDS` dict — game-specific |

---

## Rejected as domain entities

| Dump label | Classification | Reason |
| ---------- | -------------- | ------ |
| `ShapeItem` | runtime / reflection / debug metadata | Type name, not recipe |
| `ShapeDefinition` | source metadata | `$type` only |
| `MetaShapeSubPart` | source metadata | Unity wrapper |
| `MetaShapeColor` | source metadata | Unity wrapper |

---

## Inferred domain entities

| Entity | Evidence |
| ------ | -------- |
| **Shape recipe** | 70 unique `Hash` + `UniqueOperationId` |
| **Shape recipe layer** | `Layers[]` order |
| **Shape quadrant slot** | `Parts[0..3]` per layer |
| **Shape component kind** | 8 distinct `Shape.name` values |
| **Fluid color** | Shared with `fluids.json` |

---

## Human review queue

| Item | Question |
| ---- | -------- |
| `Hash` token grammar | Formal spec vs `shape_catalog.py` |
| Empty layer in JSON vs `--------` in hash | Import derives hash or stores both? |
| `ConverterQuad_LV0` vs `LV1` | Game tier semantics |
| Relationship to `shapes.json` (1170 rows) | Subset? Different export? |
