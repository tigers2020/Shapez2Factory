# Risks and Open Questions — `shapes.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| 1100 shapes not in items | Unused in captured gameplay vs future content |
| `operation_uid` gaps 1–1330 | Missing ids intentional? |
| Hash two-letter grammar | Validation rules incomplete |

## Human review

| Question |
| -------- |
| Import shapes only and drop separate items import? |
| Store `catalog_source` on recipe for items subset? |
| Expose all 1170 to planner or filter? |

## Runtime traps

- Table `ShapeDefinition`
- Using `#N` as display name in UI

## Ambiguous IDs

- shapes: `stable_id` unique but **`Hash` still preferred** domain key for cross-file joins
- items: duplicate `stable_id` — do not merge tables without hash key

## Version drift

- Large file (~1.7 MB); manifest hash mandatory in CI.

## Missing targets

- None for research ShapeHash (all resolved)
- Gameplay mapping for non-item shapes

## Deferred

| Table | Reason |
| ----- | ------ |
| `shape_recipe_gameplay_flag` | No source field |

## Highest risk

**Duplicate import from items + shapes** creating 1240 rows or conflicts. **Mitigation:** single upsert on `shape_hash`; shapes file is authoritative superset.
