# Risks and Open Questions — `raw_type_index.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| 6497 CLR types vs planner domain | Over-importing noise into query paths |
| `stable_id` collisions | Misused as PK breaks idempotency |
| `type_name` without assembly in other dumps | Ambiguous joins |

## Human review

| Question |
| -------- |
| Expose registry to planner API or import-only? |
| Exclude compiler-generated rows by default? |
| Map `assembly_name` to `manifest` DLL rows formally? |

## Runtime traps

- Table/model named `HUDDebugStats` or `ShapeOperationPaintPayload`
- Treating file as gameplay entities (buildings/items)

## Ambiguous IDs

- **`stable_id` unreliable** — use (`type_name`, `assembly_name`)
- **`type_name` alone** ambiguous across 37 assemblies

## Dynamic schema

- New game version may add thousands of types; import must stay batch-safe.

## Version drift

- `manifest.file_hashes.raw_type_index.json` — large blob, CI must hash full file.

## Missing targets

| Target | Status |
| ------ | ------ |
| Full assembly-qualified names (`Version=…`) | Not in `type_name` field |
| FK to `building_variant` | Not in JSON |
| `asset_references` | Separate content IDs |

## Deferred tables

| Table | Reason |
| ----- | ------ |
| `clr_type_member_index` | Not exported |
| `namespace_hierarchy` | Not in dump |

## Highest risk

Using **`stable_id` as UNIQUE** on 6497 rows — 114 collisions. **Mitigation:** composite UNIQUE on (`type_name`, `assembly_name`); `dump_stable_id` audit only.
