# game_data Phase 3 — Domain Coverage Gap Fill

**Date:** 2026-05-22  
**Status:** Draft — awaiting implementation plan  
**Scope:** implementation change + contract change  
**Predecessor:** Phase 2 simulation path audit (2026-05-22)  
**Coverage doc:** [`docs/domain/game_data_coverage.md`](../../domain/game_data_coverage.md)  
**JSON structure:** [`docs/domain/game_data_json_deep/`](../../domain/game_data_json_deep/)

---

## 1. Goals

Among paths handled as `ignore_audit` through Phase 2, promote **paths practically required for planner functionality** to `promoted` and store them in the ORM.

### Analysis criteria

- "Functional completeness" criterion — prioritize data required by solver/planner  
- No JSONField — all values in scalar normalized columns  
- Keep Phase approach — additional paths must be manifest-registered before import

### Analysis summary (gaps found)

| Category | File | Path | Verdict |
|---|---|---|---|
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IConveyorConfiguration.ConveyorSpeed` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IFluidPort*Configuration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.*.Rate.Value` | **PROMOTE** |
| 🔴 HIGH | `building_variants.json` | `IEntityDefinition.CustomData.All[].IPipeGateConfiguration.*.Rate.Value` | **PROMOTE** |
| 🟡 MED | `buildings.json` | `<RequiredStoreContentId>k__BackingField.Id` / `RequiredStoreContentId.Id` | **PROMOTE** |
| 🟡 MED | `buildings.json` | `<ShowAsResearchReward>k__BackingField` / `ShowAsResearchReward` | **PROMOTE** |
| 🟡 MED | `fluids.json` | `display_name_key` (row-level) | **PROMOTE** |
| 🟢 IGNORE | `building_variants.json` | `ConnectorData.TileBounds.Min/Max` | `ignore_audit:LAYOUT_METADATA` |
| 🟢 IGNORE | `building_variants.json` | `ConnectorData.AllBuildingConnectors[]._IOType` | `ignore_audit:LEGACY_FIELD` |
| 🟢 IGNORE | `building_variants.json` | `IEntityDefinition.CustomData.All[].CustomDrawData.*` | `ignore_audit:RENDER_METADATA` |

---

## 2. Architecture

### 2-A. `BuildingVariantRateConfig` (new model)

`building_variants.json` `IEntityDefinition.CustomData.All[]` is a polymorphic interface list.
Store each item's interface key (e.g. `IConveyorConfiguration`) and parameters as normalized rows.

```python
class BuildingVariantRateConfig(models.Model):
    """Per-interface physics/rate parameter extracted from CustomData.All[]."""

    variant = models.ForeignKey(
        BuildingVariant,
        on_delete=models.CASCADE,
        related_name="rate_configs",
    )
    interface_key = models.CharField(max_length=255)   # e.g. "IConveyorConfiguration"
    param_key = models.CharField(max_length=128)        # e.g. "steps_per_tick"
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    text_value = models.CharField(max_length=255, blank=True, default="")
    research_scale_id = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "interface_key", "param_key"],
                name="uq_variant_rate_config_key",
            )
        ]
        verbose_name = "building variant rate config"
        verbose_name_plural = "④ Buildings · Variant rate configs"
```

**Storage example:**

| variant | interface_key | param_key | int_value | float_value | text_value |
|---|---|---|---|---|---|
| Belt1x1 | `IConveyorConfiguration` | `steps_per_tick` | 1 | null | |
| Belt1x1 | `IConveyorConfiguration` | `research_scale_id` | null | null | `BeltSpeedUpgrade` |
| FluidPump | `IFluidPortReceiverConfiguration` | `fluid_provide_rate` | null | 0.5 | |
| FluidPump | `IFluidPortSenderConfiguration` | `fluid_consume_rate` | null | 0.5 | |

**Extract interface → param_key mapping:**

| CustomData interface | Extract path | param_key | Type |
|---|---|---|---|
| `IConveyorConfiguration` | `ConveyorSpeed.StepsPerTick.Value` | `steps_per_tick` | int |
| `IConveyorConfiguration` | `ConveyorSpeed.BaseSpeed` | `base_speed` | float |
| `IConveyorConfiguration` | `ConveyorSpeed.ResearchId.Id` | `research_scale_id` | text |
| `IFluidPortReceiverConfiguration` | `ProvidingConfiguration.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `fluid_provide_rate` | float |
| `IFluidPortSenderConfiguration` | `ConsumingConfiguration.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `fluid_consume_rate` | float |
| `ICrystalGeneratorConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `crystal_consume_rate` | float |
| `IFluidStorageConfiguration` | `ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `fluid_storage_provide_rate` | float |
| `IFluidStorageConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `fluid_storage_consume_rate` | float |
| `IPipeGateConfiguration` | `ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate.Value` | `pipe_gate_provide_rate` | float |
| `IPipeGateConfiguration` | `ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate.Value` | `pipe_gate_consume_rate` | float |

Extraction logic: use each item's top-level key in `CustomData.All[]` as the interface key.
If the same interface appears multiple times, use only the first item (add audit warning later).

### 2-B. `BuildingGroup` field additions

```python
# extracted from buildings.json / building_groups.json definition_snapshot
required_store_content_id = models.CharField(max_length=128, blank=True, default="")
show_as_research_reward = models.BooleanField(default=False)
```

Extraction paths:
- `RequiredStoreContentId.Id` (non-backing field first; fallback `<RequiredStoreContentId>k__BackingField.Id`)
- `ShowAsResearchReward` (boolean; fallback `<ShowAsResearchReward>k__BackingField`)

### 2-C. `FluidColor.display_name_key` addition

```python
display_name_key = models.CharField(max_length=512, blank=True, default="")
```

Read row-level `display_name_key` directly (already available via `row.get("display_name_key")` in importer).

---

## 3. Manifest registration

**New reason_codes** (add to `django_apps/game_data/coverage/reason_codes.py`):

```python
LAYOUT_METADATA = "LAYOUT_METADATA"       # ConnectorData TileBounds etc. — placement rendering only
LEGACY_FIELD = "LEGACY_FIELD"             # _IOType etc. — backward-compat legacy fields
RENDER_METADATA = "RENDER_METADATA"       # CustomDrawData etc. — rendering only
NESTED_ENTITY_DEF = "NESTED_ENTITY_DEF"  # CustomData.All[].Definitions[] recursive entities
REFLECTION_CACHE = "REFLECTION_CACHE"     # DataPerTypeCache etc. — CLR reflection cache
```

Add to `django_apps/game_data/coverage/manifest.py`:

```python
# Phase 3 PROMOTED
"building_variants.json:IEntityDefinition.CustomData.All[].IConveyorConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IFluidStorageConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"building_variants.json:IEntityDefinition.CustomData.All[].IPipeGateConfiguration": (PROMOTED, "BuildingVariantRateConfig"),
"buildings.json:RequiredStoreContentId": (PROMOTED, "BuildingGroup.required_store_content_id"),
"buildings.json:ShowAsResearchReward": (PROMOTED, "BuildingGroup.show_as_research_reward"),

# Phase 3 IGNORE_AUDIT
"building_variants.json:ConnectorData.TileBounds": (IGNORE_AUDIT, "LAYOUT_METADATA"),
"building_variants.json:ConnectorData.AllBuildingConnectors[]._IOType": (IGNORE_AUDIT, "LEGACY_FIELD"),
"building_variants.json:IEntityDefinition.CustomData.All[].CustomDrawData": (IGNORE_AUDIT, "RENDER_METADATA"),
"building_variants.json:IEntityDefinition.CustomData.All[].Definitions[]": (IGNORE_AUDIT, "NESTED_ENTITY_DEF"),
"building_variants.json:IEntityDefinition.CustomData.DataPerTypeCache": (IGNORE_AUDIT, "REFLECTION_CACHE"),
```

---

## 4. Invariants

```text
1. No JSONField on BuildingVariantRateConfig.
2. (variant, interface_key, param_key) combination is unique.
3. On CustomData.All[] parse failure, skip that variant rate config and record via ctx.record_unknown.
4. BuildingGroup.required_store_content_id == "" means no DLC restriction.
5. FluidColor.display_name_key addition does not change existing FK/UK.
6. All new paths may be imported only after manifest registration.
```

---

## 5. Data flow

```
building_variants.json
  └── _import_building_variants()  (importer.py)
        ├── BuildingVariant (existing)
        ├── BuildingConnector (existing)
        ├── BuildingFootprintTile (existing)
        └── BuildingVariantRateConfig (NEW) ← CustomData.All[] parsing

buildings.json / building_groups.json
  └── _upsert_building_group()  (importer.py)
        └── BuildingGroup (add required_store_content_id, show_as_research_reward)

fluids.json
  └── _import_fluids()  (importer.py)
        └── FluidColor (add display_name_key)
```

---

## 6. Test plan

| Test file | Verification |
|---|---|
| `tests/unit/game_data/test_building_variant_rate_config.py` | ConveyorSpeed extraction, fluid rate extraction, interface_key accuracy, multiple interface handling |
| `tests/unit/game_data/test_building_group_flags.py` | correct extraction of required_store_content_id, show_as_research_reward |
| `tests/unit/game_data/test_fluid_color_display_name.py` | verify display_name_key storage |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | verify new manifest path registration (extend existing file) |
| Existing regression | `test_simulation_path_coverage.py` — unchanged green |

**Test data:** Extract one belt/fluid variant fixture each from actual `documents/game_data/` JSON.

---

## 7. Migration strategy

1. `BuildingVariantRateConfig` new table — create migration
2. `BuildingGroup.required_store_content_id`, `show_as_research_reward` — migration (not nullable, has default)
3. `FluidColor.display_name_key` — migration (default `""`)
4. After migration, re-run `import_game_data --source documents/game_data`
5. Regenerate `dumpdata game_data` → update `game_data_backup/game_data_dump.json`

---

## 8. Risks

| Risk | Level | Response |
|---|---|---|
| `CustomData.All[]` structure varies by version | MEDIUM | parse failure recorded via `record_unknown`, not crash |
| Only first used when same interface_key appears multiple times | LOW | record warning, auditable later |
| New manifest paths conflict with existing coverage tests | LOW | update tests alongside manifest registration |
| Both `k__BackingField` and non-backing field values exist | LOW | read non-backing first, backing field fallback |

---

## 9. Out of Scope

- `research_unlocks.json` Rewards modeling — separate Phase
- `building_variants.json ConnectorData.TileBounds` normalization — `ignore_audit` registration only
- `simulation_systems.json` additional paths — completed in Phase 2
- Existing `ignore_audit` paths (Assembly reflection, Runtime delegate, etc.) — no change

---

## 10. References

- Phase 1-2 spec: [`docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md`](2026-05-22-game-data-domain-complete-coverage-design.md)
- JSON deep docs: [`docs/domain/game_data_json_deep/`](../../domain/game_data_json_deep/)
- Coverage manifest: [`django_apps/game_data/coverage/manifest.py`](../../../django_apps/game_data/coverage/manifest.py)
- Reason codes: [`django_apps/game_data/coverage/reason_codes.py`](../../../django_apps/game_data/coverage/reason_codes.py)
