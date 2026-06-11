# Risks and Open Questions — `building_groups.json`

## Fields with uncertain meaning

| Field / area | Risk |
| ------------ | ---- |
| `simulation_parameters` vs snapshot `IsTransportBuilding` | Duplicated bool — which is authoritative if they diverge? |
| `StructureOverview` | Wiki/video UI — planner need unclear |
| `RequiredStoreContentId` | DLC/store gating — no target table in bundle |
| `PipetteOverrideId` | Usually empty — semantics when set |
| Embedded `Definitions[]` vs `building_variants.json` | Snapshots may differ in hash though same `Id.Name` |
| `_Definitions` duplicate array | Importer must not double-count members |

---

## Inferred entities requiring human review

| Entity | Question |
| ------ | -------- |
| `building_group` vs `building` | Two tables needed, or merge on `group_key` with registry hash optional? |
| `building_group` registry `stable_id` | Expose to planner or internal import only? |
| `building_group_member` cycle resolution | Algorithm proof for 34 `$cycle` rows |
| `building_placement_rule` | Which of 8 rule kinds are simulation-critical? |
| Separate file purpose | Why ship 13 MB duplicate of `buildings.json`? |

---

## Runtime metadata mistaken for domain data

| Signal | Risk |
| ------ | ---- |
| `BuildingDefinitionGroup` | Django model name collision |
| 152 `$type` values | Table explosion |
| 5,564 `k__BackingField` keys | Accidental columns |
| `$unity` / `instance_id` on icons | Treating Unity ids as stable FKs |
| Long `IEntityConnectorData<...>` property names | Schema mirroring |

---

## Ambiguous IDs

| ID | Issue |
| -- | ----- |
| `registry_stable_id` (groups) vs `stable_id` (buildings) | Same snapshot, different hash — never interchange |
| `LazyText[...]` vs plain `display_name_key` in buildings | Two display reference styles |
| `$cycle` definition members | Not a variant name — needs graph resolver |

---

## Dynamic schemas

| Scenario | Impact |
| -------- | ------ |
| Group count ≠ 67 | Manifest hash + CI count guard |
| New `DefaultPreferredPlacementMode` | Enum migration |
| Extra `Definitions` member | Member cardinality change |
| `Definitions` embed new fields | `unknown_property` + variant parser update |

File is homogeneous at envelope level but **highly variable** inside `Definitions[]` (1–13 members).

---

## Possible version drift

- `manifest.game_version`: `unknown+1.0.3-rc3`
- `dump_schema_version`: `1.0.0`
- Size ~13 MB — sensitive to embedded variant growth
- `translations.json` incomplete — LazyText keys may not resolve until export fixed

---

## Missing cross-reference targets

| Consumer | Status |
| -------- | ------ |
| `translations.json` | Incomplete per manifest |
| `research_unlocks.json` | Textual only (67/67) — FK not extracted |
| `toolbar_entries.json` | 57/67 textual hits |
| Application code | No importer in repo yet |
| `belts_pipes_transport` | Indirect via variants, not group guid |

---

## Tables that should not be implemented yet

| Table | Reason |
| ----- | ------ |
| `building_group_raw` | Forbidden |
| Per-`$type` tables (152) | Reflection mirror |
| `unity_sprite_instance` | Engine debug |
| Full `structure_overview_slot` | Spec unclear |
| Relational expansion of all `CustomData` | Defer to simulation domain |

**Implement first:** `building_group`, `building_group_member`, `building_group_simulation_setting`, `building_group_localization_ref`, with snapshot dedupe to `buildings` import.

---

## Duplication risk (critical)

| Duplication | Size impact |
| ----------- | ----------- |
| `building_groups.json` vs `buildings.json` snapshot | 67 identical snapshots |
| Embedded variants vs `building_variants.json` | Up to 97 full variant graphs duplicated inside groups file |

**Mandatory:** content-hash dedupe before persisting geometry.

---

## Summary risk level

| Area | Level |
| ---- | ----- |
| Envelope | **Low** (67 flat rows) |
| Nested snapshot | **Very high** (13 MB, reflection) |
| FK to buildings/variants | **Low** (guid + name resolved) |
| Cycle members | **Medium** (34 graph refs) |
| Planner integration | **Medium** (research/toolbar textual) |
