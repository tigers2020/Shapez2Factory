# Risks and Open Questions — `items.json`

## Uncertain field meaning

| Field / pattern | Risk | Mitigation |
| --------------- | ---- | ---------- |
| Two-char `Hash` tokens (`Cu`, `Ck`, `P-`) | May drift from `shape_catalog.py` | Golden tests per sample; document grammar |
| `ConverterQuad_LV0` vs `LV1` | Tier semantics unknown | Human review with building data |
| Empty `Shape`/`Color` vs hash `-` / `--------` | Dual representation | Define canonical empty slot rules on import |

## Inferred entities needing human review

| Entity | Question |
| ------ | -------- |
| `shape_recipe` vs `shapes.json` | Are 70 recipes a subset of 1170 shape definitions? |
| `hash_token` on slot | Store denormalized or compute on read? |
| `catalog_shape_code` on `shape_component_kind` | Manual map table vs derived |

## Runtime metadata mistaken for domain data

| Trap | Correct handling |
| ---- | ---------------- |
| Table named `ShapeItem` | Reject; use `shape_recipe` |
| PK = `stable_id` | Reject; non-unique |
| PK = `instance_id` | Reject |
| Using `display_name_key` for UI | Needs `translations.json` |

## Ambiguous IDs

| ID | Issue |
| -- | ----- |
| `stable_id` | Same for all 70 rows |
| `source_guid` | Constant `ShapeItem` |
| `Id.Uid` vs `UniqueOperationId` | Redundant — pick one canonical column |

## Dynamic schemas

- Low risk: structure stable across 70 rows.
- Watch for new `Shape.name` values in future dumps → `unknown_property` + enum test failure.

## Version drift

- Manifest SHA-256 must be tracked on every `items.json` change.
- Game patch may add recipes without changing envelope shape.

## Missing cross-reference targets

| Target | Status |
| ------ | ------ |
| `shapes.json` linkage | **Open** — overlap analysis incomplete |
| Research / unlock | No direct refs in items |
| Building recipes | Indirect via painted shapes in simulation |

## Tables deferred (do not implement yet)

| Table | Reason |
| ----- | ------ |
| `shape_hash_grammar` | Until token spec approved |
| `shape_recipe_translation` | Blocked on `translations.json` analysis |
| M2M recipe ↔ building | No IDs in source |

## Summary risk

**Highest risk:** treating 70 dump rows as 70 unique `stable_id` entities or mirroring `Layers[]` into a JSONField — breaks idempotency and planner contracts. **Mitigation:** `operation_uid` + `shape_hash` as business keys, normalized layer/slot tables, fluids FK first.
