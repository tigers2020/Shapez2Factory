# Risks and Open Questions — `toolbar_entries.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| 5.7 MB nested blobs | Import memory/time |
| Dual tree representation (`Children` vs flat paths) | Drift if inconsistent |
| 57 vs 78 building keys | Duplicate placer/building combos |

## Human review

| Question |
| -------- |
| FK `building_definition_key` → which building table? |
| Import `simulation_parameters` or ignore? |
| Model all `BuildingDefinition` scalars or minimal set? |

## Runtime traps

- Columns named `IPresentableToolbarElementData.Icon`
- Table `GroupToolbarElementData`

## Ambiguous IDs

- `tree_path` is human-readable but canonical in this dump
- `PlacerId` alone not globally unique without kind

## Deferred

| Table | Reason |
| ----- | ------ |
| `toolbar_localization` | translations empty |
| `building_definition_full_policy` | 20+ fields |

## Highest risk

**Mirroring `BuildingDefinition` into domain JSON** — duplicates `building_groups` and bloats DB. **Mitigation:** extract `building_definition_key` + scalars; join building catalog separately.
