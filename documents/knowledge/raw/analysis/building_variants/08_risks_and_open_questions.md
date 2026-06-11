# Risks and Open Questions — `building_variants.json`

## Fields with uncertain meaning

| Item | Risk |
| ---- | ---- |
| `building_stable_id` always empty | Parent FK deferred — membership import must backfill |
| `CustomData` mostly `$cycle` | Full simulation config not extracted |
| `LabelDefaultInternalVariant` (0 connectors) | Special-case building or incomplete dump |
| `_IOType` vs `IOType` | Redundant fields on some connectors |
| Partial embed in `building_groups.json` | Risk of overwriting canonical variant with truncated graph |

---

## Inferred entities requiring human review

| Entity | Question |
| ------ | -------- |
| `building_variant` vs internal name only | Is `stable_id` needed in planner APIs? |
| `is_mirrored` suffix rule | Sufficient vs explicit `mirrored_from_id` FK |
| `building_variant_legacy_io` | Required for simulation parity? |
| `building_variant_custom_config` | Which of 156 `$type` nodes matter for factory planner? |
| Mirrored variants (34) | Auto-pair with non-mirrored base variant? |

---

## Runtime metadata mistaken for domain data

| Signal | Risk |
| ------ | ---- |
| `BuildingDefinition` as model name | Collision with dump label |
| 156 `$type` strings | Table explosion if mirrored literally |
| 11,787 `k__BackingField` keys | Accidental schema import |
| `IEntityConnectorData<...>` duplicate trees | Double connector rows |
| Unity refs inside deep CustomData | `instance_id` as FK |

---

## Ambiguous IDs

| ID | Issue |
| -- | ----- |
| `stable_id` | Hash algorithm not documented |
| `source_guid` vs `Id.Name` | Identical today — which is canonical for imports? |
| `$cycle` in groups | Resolving to mirrored `internal_name` needs graph rules |

---

## Dynamic schemas

| Scenario | Impact |
| -------- | ------ |
| Variant count ≠ 131 | CI guard + manifest hash fail |
| New connector `$type` | Extend `connector_role` enum |
| New footprint sizes | Validate tile bounds |
| Populated `building_stable_id` in future dumps | Migration + FK backfill |

---

## Possible version drift

- Game `unknown+1.0.3-rc3`, schema `1.0.0`
- File size ~3.8 MB sensitive to embedded custom data growth
- Asteroid lab tests reference `*InternalVariant` strings — keep naming stable

---

## Missing cross-reference targets

| Target | Status |
| ------ | ------ |
| `building_stable_id` → building/group | Empty |
| `translations.json` | Incomplete |
| Explicit variant ↔ prefab map | Only indirect via transport |
| In-repo Django importer | Not implemented |

---

## Tables that should not be implemented yet

| Table | Reason |
| ----- | ------ |
| `building_variants_raw` | Forbidden |
| Per-`$type` simulation tables (156) | Reflection |
| `unity_mesh_reference` | Engine debug |
| Full `legacy_io_graph` | `$cycle` complexity |

**Implement first:** `building_variant`, `building_connector`, `building_footprint_tile`.

---

## Duplication risk

| Duplication | Mitigation |
| ----------- | ---------- |
| 97 variants embedded in `building_groups.json` | Import from this file only; groups import membership pointers |
| 9 variants in `belts_pipes_transport` | Hash-equal — skip geometry re-parse |
| Same `internal_name` in multiple files | Single canonical row keyed by `internal_name` |

---

## Summary risk level

| Area | Level |
| ---- | ----- |
| Envelope | **Low** |
| Connectors/tiles | **Medium** (well-structured) |
| CustomData / legacy | **High** |
| Parent FK | **High** (empty `building_stable_id`) |
| Planner integration | **Medium** (simulation_systems references names) |
