# game_data Phase 3 — Domain Coverage Gap Fill Implementation Plan

> **pytest output:** [`AGENTS.md`](../../../AGENTS.md) · [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote ConveyorSpeed and fluid rates from `building_variants.json`, DLC/research reward flags from `buildings.json`, and display_name_key from `fluids.json` to ORM and update coverage manifest.

**Architecture:** Store CustomData.All[] polymorphic settings as interface key + param key scalar rows in new normalized `BuildingVariantRateConfig` table. Add fields only to existing `BuildingGroup`, `FluidColor`. Dedicated `custom_data_extractor.py` module owns parsing logic.

**Tech Stack:** Django ORM, pytest, ruff, mypy, black

---

## File Map

| File | Work |
|---|---|
| `django_apps/game_data/coverage/reason_codes.py` | modify — add 5 new reason codes |
| `django_apps/game_data/models/shapes.py` | modify — add `FluidColor.display_name_key` |
| `django_apps/game_data/models/buildings.py` | modify — `BuildingGroup` 2 fields, new `BuildingVariantRateConfig` class |
| `django_apps/game_data/models/__init__.py` | modify — export `BuildingVariantRateConfig` |
| `django_apps/game_data/services/identifiers.py` | modify — add `canonical_variant_rate_config` |
| `django_apps/game_data/importers/custom_data_extractor.py` | new — CustomData.All[] parser |
| `django_apps/game_data/importers/importer.py` | modify — update 3 importer functions |
| `django_apps/game_data/coverage/manifest.py` | modify — register Phase 3 promoted/ignore_audit |
| `django_apps/game_data/migrations/0025_phase3_coverage_gap_fill.py` | new — migration |
| `tests/unit/game_data/test_building_variant_rate_config.py` | new |
| `tests/unit/game_data/test_building_group_flags.py` | new |
| `tests/unit/game_data/test_fluid_color_display_name.py` | new |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | modify — add Phase 3 manifest key verification |

---

## Task 1: reason_codes.py — add 5 new codes

**Files:**
- Modify: `django_apps/game_data/coverage/reason_codes.py`

- [ ] **Step 1: Add 5 codes at end of file**

Current file (`django_apps/game_data/coverage/reason_codes.py`):
```python
"""Reason codes for UnknownProperty and coverage ignore_audit entries."""

REFLECTION_METADATA = "REFLECTION_METADATA"
RUNTIME_DELEGATE = "RUNTIME_DELEGATE"
SIMULATION_FACTORY_STUB = "SIMULATION_FACTORY_STUB"
RUNTIME_UNITY_METADATA = "RUNTIME_UNITY_METADATA"
UNMAPPED_DOMAIN_CANDIDATE = "UNMAPPED_DOMAIN_CANDIDATE"
```

After addition:
```python
"""Reason codes for UnknownProperty and coverage ignore_audit entries."""

REFLECTION_METADATA = "REFLECTION_METADATA"
RUNTIME_DELEGATE = "RUNTIME_DELEGATE"
SIMULATION_FACTORY_STUB = "SIMULATION_FACTORY_STUB"
RUNTIME_UNITY_METADATA = "RUNTIME_UNITY_METADATA"
UNMAPPED_DOMAIN_CANDIDATE = "UNMAPPED_DOMAIN_CANDIDATE"

# Phase 3 — building_variants.json CustomData ignore paths
LAYOUT_METADATA = "LAYOUT_METADATA"       # ConnectorData TileBounds — placement rendering only
LEGACY_FIELD = "LEGACY_FIELD"             # _IOType etc. — backward-compat legacy fields
RENDER_METADATA = "RENDER_METADATA"       # CustomDrawData — rendering only
NESTED_ENTITY_DEF = "NESTED_ENTITY_DEF"  # CustomData.All[].Definitions[] recursive entities
REFLECTION_CACHE = "REFLECTION_CACHE"     # DataPerTypeCache — CLR reflection cache
```

- [ ] **Step 2: ruff check**

```bash
python -m ruff check django_apps/game_data/coverage/reason_codes.py
```
Expected: no errors

- [ ] **Step 3: commit**

```bash
git add django_apps/game_data/coverage/reason_codes.py
git commit -m "feat(game_data): add Phase 3 reason codes for CustomData ignore paths"
```

---

## Task 2: Add FluidColor.display_name_key field

**Files:**
- Modify: `django_apps/game_data/models/shapes.py`
- Modify: `django_apps/game_data/importers/importer.py`
- Test: `tests/unit/game_data/test_fluid_color_display_name.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/game_data/test_fluid_color_display_name.py`:

```python
"""FluidColor.display_name_key import coverage."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import FluidColor, ImportBatch


@pytest.mark.django_db
def test_fluid_color_display_name_key_stored(db: None) -> None:
    batch = ImportBatch.objects.create(
        manifest_self_hash="test-hash-fluid",
        batch_name="test",
        game_version="1.0",
    )
    fc = FluidColor.objects.create(
        canonical_id="fluid:TestColor",
        import_batch=batch,
        color_name="TestColor",
        display_name_key="fluids.test-color",
        source_stable_id="stb-1",
        source_row_index=0,
    )
    reloaded = FluidColor.objects.get(pk=fc.pk)
    assert reloaded.display_name_key == "fluids.test-color"


@pytest.mark.django_db
def test_fluid_color_display_name_key_default_empty(db: None) -> None:
    batch = ImportBatch.objects.create(
        manifest_self_hash="test-hash-fluid2",
        batch_name="test",
        game_version="1.0",
    )
    fc = FluidColor.objects.create(
        canonical_id="fluid:NoName",
        import_batch=batch,
        color_name="NoName",
        source_stable_id="stb-2",
        source_row_index=1,
    )
    assert fc.display_name_key == ""
```

- [ ] **Step 2: Confirm test failure**

```bash
python -m pytest tests/unit/game_data/test_fluid_color_display_name.py -v
```
Expected: FAIL — `FluidColor` has no field `display_name_key`

- [ ] **Step 3: Add field to FluidColor**

`FluidColor` class in `django_apps/game_data/models/shapes.py`:

```python
class FluidColor(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="fluid_colors"
    )
    color_name = models.CharField(max_length=64, unique=True)
    fluid_kind = models.CharField(max_length=32, default="ColorFluid")
    display_name_key = models.CharField(max_length=512, blank=True, default="")  # NEW
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    source_row_index = models.PositiveIntegerField()
```

- [ ] **Step 4: Update importer — store display_name_key**

`_import_fluids` method in `django_apps/game_data/importers/importer.py`:

```python
def _import_fluids(self) -> None:
    assert self.ctx is not None
    rows = load_json(self._path("fluids.json"))
    for i, row in enumerate(rows):
        color_name = dig(row, "definition_snapshot", "Color", "name", default="")
        if not color_name:
            continue
        cid = identifiers.canonical_fluid_color(color_name)
        FluidColor.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": self.ctx.batch,
                "color_name": color_name,
                "display_name_key": str(row.get("display_name_key", "")),  # NEW
                "source_stable_id": str(row.get("stable_id", "")),
                "source_row_index": i,
            },
        )
        self.ctx.bump("fluid_color")
```

- [ ] **Step 5: Create migration (combine with Task 4 migration — skip here, batch after Task 4)**

- [ ] **Step 6: Confirm tests pass (after migration)**

```bash
python -m pytest tests/unit/game_data/test_fluid_color_display_name.py -v
```
Expected: PASS

---

## Task 3: Add 2 BuildingGroup fields

**Files:**
- Modify: `django_apps/game_data/models/buildings.py`
- Modify: `django_apps/game_data/importers/importer.py`
- Test: `tests/unit/game_data/test_building_group_flags.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/game_data/test_building_group_flags.py`:

```python
"""BuildingGroup DLC/reward flags import coverage."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import BuildingGroup, ImportBatch


def _make_batch(suffix: str) -> ImportBatch:
    return ImportBatch.objects.create(
        manifest_self_hash=f"test-hash-bg-{suffix}",
        batch_name="test",
        game_version="1.0",
    )


@pytest.mark.django_db
def test_building_group_required_store_content_id_stored(db: None) -> None:
    batch = _make_batch("a")
    bg = BuildingGroup.objects.create(
        canonical_id="building_group:TestGroup",
        import_batch=batch,
        group_key="TestGroup",
        display_profile=BuildingGroup.DisplayProfile.PLAIN,
        required_store_content_id="dlc-premium-pack",
        source_row_index=0,
    )
    assert BuildingGroup.objects.get(pk=bg.pk).required_store_content_id == "dlc-premium-pack"


@pytest.mark.django_db
def test_building_group_required_store_content_id_default_empty(db: None) -> None:
    batch = _make_batch("b")
    bg = BuildingGroup.objects.create(
        canonical_id="building_group:FreeGroup",
        import_batch=batch,
        group_key="FreeGroup",
        display_profile=BuildingGroup.DisplayProfile.PLAIN,
        source_row_index=0,
    )
    assert bg.required_store_content_id == ""


@pytest.mark.django_db
def test_building_group_show_as_research_reward_stored(db: None) -> None:
    batch = _make_batch("c")
    bg = BuildingGroup.objects.create(
        canonical_id="building_group:RewardGroup",
        import_batch=batch,
        group_key="RewardGroup",
        display_profile=BuildingGroup.DisplayProfile.PLAIN,
        show_as_research_reward=True,
        source_row_index=0,
    )
    assert BuildingGroup.objects.get(pk=bg.pk).show_as_research_reward is True


@pytest.mark.django_db
def test_building_group_show_as_research_reward_default_false(db: None) -> None:
    batch = _make_batch("d")
    bg = BuildingGroup.objects.create(
        canonical_id="building_group:DefaultGroup",
        import_batch=batch,
        group_key="DefaultGroup",
        display_profile=BuildingGroup.DisplayProfile.PLAIN,
        source_row_index=0,
    )
    assert bg.show_as_research_reward is False
```

- [ ] **Step 2: Confirm test failure**

```bash
python -m pytest tests/unit/game_data/test_building_group_flags.py -v
```
Expected: FAIL — `BuildingGroup` has no field `required_store_content_id`

- [ ] **Step 3: Add fields to BuildingGroup model**

Add 2 fields to `BuildingGroup` class in `django_apps/game_data/models/buildings.py`:

```python
class BuildingGroup(models.Model):
    class DisplayProfile(models.TextChoices):
        PLAIN = "plain", "buildings.json"
        LAZY = "lazy_overlay", "building_groups.json"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="building_groups"
    )
    group_key = models.CharField(max_length=255, unique=True)
    registry_stable_id = models.CharField(max_length=64, blank=True, default="")
    display_profile = models.CharField(max_length=16, choices=DisplayProfile.choices)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    is_transport_building = models.BooleanField(default=False)
    placement_mode = models.CharField(max_length=64, blank=True, default="")
    player_buildable = models.BooleanField(default=True)
    selectable = models.BooleanField(default=True)
    removable = models.BooleanField(default=True)
    auto_connect = models.BooleanField(default=False)
    required_store_content_id = models.CharField(max_length=128, blank=True, default="")  # NEW
    show_as_research_reward = models.BooleanField(default=False)                           # NEW
    source_row_index = models.PositiveIntegerField()
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="building_groups",
    )
```

- [ ] **Step 4: Update importer `_upsert_building_group`**

Add 2 keys to `BuildingGroup.objects.update_or_create` defaults in `_upsert_building_group` in `django_apps/game_data/importers/importer.py`:

```python
group, _ = BuildingGroup.objects.update_or_create(
    canonical_id=cid,
    defaults={
        "import_batch": self.ctx.batch,
        "group_key": group_key,
        "registry_stable_id": str(row.get("stable_id", "")),
        "display_profile": profile,
        "display_name_key": str(row.get("display_name_key", "")),
        "is_transport_building": bool(dig(snap, "IsTransportBuilding", default=False)),
        "placement_mode": str(dig(snap, "DefaultPreferredPlacementMode", default="")),
        "player_buildable": bool(dig(snap, "PlayerBuildable", default=True)),
        "selectable": bool(dig(snap, "Selectable", default=True)),
        "removable": bool(dig(snap, "Removable", default=True)),
        "auto_connect": bool(dig(snap, "AutoConnect", default=False)),
        # Phase 3: backing field first, no fallback (empty string = no restriction)
        "required_store_content_id": str(
            dig(snap, "RequiredStoreContentId", "Id", default="")
            or dig(snap, "<RequiredStoreContentId>k__BackingField", "Id", default="")
            or ""
        ),
        "show_as_research_reward": bool(
            snap.get("ShowAsResearchReward")
            or snap.get("<ShowAsResearchReward>k__BackingField")
            or False
        ),
        "source_row_index": index,
        "source_object": src,
    },
)
```

- [ ] **Step 5: Batch migration after Task 4 — skip here**

---

## Task 4: Add BuildingVariantRateConfig model + identifier

**Files:**
- Modify: `django_apps/game_data/models/buildings.py`
- Modify: `django_apps/game_data/models/__init__.py`
- Modify: `django_apps/game_data/services/identifiers.py`
- Create: `django_apps/game_data/migrations/0025_phase3_coverage_gap_fill.py`

- [ ] **Step 1: Add `BuildingVariantRateConfig` model**

Add at end of `django_apps/game_data/models/buildings.py` (after existing `TransportBuildingRegistry`):

```python
class BuildingVariantRateConfig(models.Model):
    """Per-interface physics/rate parameter extracted from CustomData.All[].

    interface_key: top-level interface name in each CustomData.All[] item
      e.g. "IConveyorConfiguration", "IFluidPortReceiverConfiguration"
    param_key: specific parameter within that interface
      e.g. "steps_per_tick", "fluid_provide_rate"
    Exactly one of int_value / float_value / text_value is non-null/non-empty.
    research_scale_id: ResearchUpgrade key that scales this parameter (if any).
    """

    canonical_id = models.CharField(max_length=512, unique=True)
    variant = models.ForeignKey(
        BuildingVariant,
        on_delete=models.CASCADE,
        related_name="rate_configs",
    )
    interface_key = models.CharField(max_length=255)
    param_key = models.CharField(max_length=128)
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
        ordering = ["interface_key", "param_key"]

    def __str__(self) -> str:
        return f"{self.variant.internal_name} / {self.interface_key}.{self.param_key}"
```

- [ ] **Step 2: Add `__init__.py` export**

Add to import block and `__all__` list in `django_apps/game_data/models/__init__.py`:

```python
# import block (modify buildings import line):
from django_apps.game_data.models.buildings import (
    BuildingConnector,
    BuildingFootprintTile,
    BuildingGroup,
    BuildingGroupMember,
    BuildingLocalizationOverlay,
    BuildingPlacementRule,
    BuildingSimulationSetting,
    BuildingVariant,
    BuildingVariantRateConfig,   # NEW
    TransportBuildingRegistry,
)

# add to __all__ list (alphabetical):
"BuildingVariantRateConfig",
```

- [ ] **Step 3: Add canonical function to identifiers.py**

Add after `canonical_footprint_tile` in `django_apps/game_data/services/identifiers.py`:

```python
def canonical_variant_rate_config(
    variant_cid: str, interface_key: str, param_key: str
) -> str:
    return _slug(variant_cid, "rate", interface_key, param_key)
```

- [ ] **Step 4: Batch create migration (all Task 2·3·4 changes)**

```bash
python manage.py makemigrations game_data --name phase3_coverage_gap_fill
```

Expected output:
```
Migrations for 'game_data':
  django_apps/game_data/migrations/0025_phase3_coverage_gap_fill.py
    - Add field display_name_key to fluidcolor
    - Add field required_store_content_id to buildinggroup
    - Add field show_as_research_reward to buildinggroup
    - Create model BuildingVariantRateConfig
```

- [ ] **Step 5: Apply migration**

```bash
$env:DJANGO_USE_SQLITE = "1"
python manage.py migrate game_data
```

Expected: `OK`

- [ ] **Step 6: Confirm Task 2·3 tests pass**

```bash
python -m pytest tests/unit/game_data/test_fluid_color_display_name.py tests/unit/game_data/test_building_group_flags.py -v
```
Expected: PASS (8 tests)

- [ ] **Step 7: ruff + mypy**

```bash
python -m ruff check django_apps/game_data/models/buildings.py django_apps/game_data/models/shapes.py django_apps/game_data/services/identifiers.py
python -m mypy django_apps/game_data/models/buildings.py django_apps/game_data/services/identifiers.py
```
Expected: no errors

- [ ] **Step 8: commit**

```bash
git add django_apps/game_data/models/ django_apps/game_data/services/identifiers.py django_apps/game_data/migrations/0025_phase3_coverage_gap_fill.py tests/unit/game_data/test_fluid_color_display_name.py tests/unit/game_data/test_building_group_flags.py
git commit -m "feat(game_data): add BuildingVariantRateConfig model and BuildingGroup/FluidColor phase3 fields"
```

---

## Task 5: Create new CustomData extractor module

**Files:**
- Create: `django_apps/game_data/importers/custom_data_extractor.py`
- Test: `tests/unit/game_data/test_building_variant_rate_config.py` (partial)

- [ ] **Step 1: Write failing unit test (extraction logic only)**

Create `tests/unit/game_data/test_building_variant_rate_config.py`:

```python
"""BuildingVariantRateConfig extraction and import tests."""

from __future__ import annotations

import pytest

from django_apps.game_data.importers.custom_data_extractor import (
    RateParam,
    extract_rate_params,
)


# ---------------------------------------------------------------------------
# extract_rate_params unit tests (no DB)
# ---------------------------------------------------------------------------

def _custom_data(all_items: list[dict]) -> dict:
    return {"IEntityDefinition": {"CustomData": {"All": all_items}}}


def test_extract_conveyor_steps_per_tick() -> None:
    snap = _custom_data([
        {
            "IConveyorConfiguration": {
                "ConveyorSpeed": {
                    "StepsPerTick": {"Value": 2},
                    "BaseSpeed": 1.5,
                    "ResearchId": {"Id": "BeltSpeed"},
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    keys = {p.param_key for p in params}
    assert "steps_per_tick" in keys
    assert "base_speed" in keys
    steps = next(p for p in params if p.param_key == "steps_per_tick")
    assert steps.int_value == 2
    assert steps.research_scale_id == "BeltSpeed"
    base = next(p for p in params if p.param_key == "base_speed")
    assert abs(base.float_value - 1.5) < 1e-6


def test_extract_fluid_receiver_provide_rate() -> None:
    snap = _custom_data([
        {
            "IFluidPortReceiverConfiguration": {
                "ProvidingConfiguration": {
                    "IProvidingFluidContainerConfiguration": {
                        "ProvidingRate": {"Value": 0.5}
                    }
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    assert len(params) == 1
    assert params[0].interface_key == "IFluidPortReceiverConfiguration"
    assert params[0].param_key == "fluid_provide_rate"
    assert abs(params[0].float_value - 0.5) < 1e-6


def test_extract_fluid_sender_consume_rate() -> None:
    snap = _custom_data([
        {
            "IFluidPortSenderConfiguration": {
                "ConsumingConfiguration": {
                    "IConsumingFluidContainerConfiguration": {
                        "ConsumingRate": {"Value": 0.25}
                    }
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    assert params[0].param_key == "fluid_consume_rate"
    assert abs(params[0].float_value - 0.25) < 1e-6


def test_extract_crystal_gen_consume_rate() -> None:
    snap = _custom_data([
        {
            "ICrystalGeneratorConfiguration": {
                "ContainerConfig": {
                    "IConsumingFluidContainerConfiguration": {
                        "ConsumingRate": {"Value": 0.1}
                    }
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    assert params[0].param_key == "crystal_consume_rate"


def test_extract_fluid_storage_both_rates() -> None:
    snap = _custom_data([
        {
            "IFluidStorageConfiguration": {
                "ContainerConfig": {
                    "IProvidingFluidContainerConfiguration": {
                        "ProvidingRate": {"Value": 1.0}
                    },
                    "IConsumingFluidContainerConfiguration": {
                        "ConsumingRate": {"Value": 2.0}
                    },
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    keys = {p.param_key for p in params}
    assert "fluid_storage_provide_rate" in keys
    assert "fluid_storage_consume_rate" in keys


def test_extract_pipe_gate_both_rates() -> None:
    snap = _custom_data([
        {
            "IPipeGateConfiguration": {
                "ContainerConfig": {
                    "IProvidingFluidContainerConfiguration": {
                        "ProvidingRate": {"Value": 0.3}
                    },
                    "IConsumingFluidContainerConfiguration": {
                        "ConsumingRate": {"Value": 0.3}
                    },
                }
            }
        }
    ])
    params = extract_rate_params(snap)
    keys = {p.param_key for p in params}
    assert "pipe_gate_provide_rate" in keys
    assert "pipe_gate_consume_rate" in keys


def test_extract_unknown_interface_returns_empty() -> None:
    snap = _custom_data([{"ISomeUnknownInterface": {"Foo": 1}}])
    params = extract_rate_params(snap)
    assert params == []


def test_extract_empty_custom_data_returns_empty() -> None:
    assert extract_rate_params({}) == []
    assert extract_rate_params({"IEntityDefinition": {}}) == []
    assert extract_rate_params({"IEntityDefinition": {"CustomData": {"All": []}}}) == []


def test_extract_multiple_interfaces_in_one_variant() -> None:
    snap = _custom_data([
        {"IConveyorConfiguration": {"ConveyorSpeed": {"StepsPerTick": {"Value": 1}}}},
        {"IFluidPortReceiverConfiguration": {
            "ProvidingConfiguration": {
                "IProvidingFluidContainerConfiguration": {"ProvidingRate": {"Value": 0.5}}
            }
        }},
    ])
    params = extract_rate_params(snap)
    ikeys = {p.interface_key for p in params}
    assert "IConveyorConfiguration" in ikeys
    assert "IFluidPortReceiverConfiguration" in ikeys
```

- [ ] **Step 2: Confirm test failure**

```bash
python -m pytest tests/unit/game_data/test_building_variant_rate_config.py -v
```
Expected: FAIL — `ModuleNotFoundError: custom_data_extractor`

- [ ] **Step 3: Implement custom_data_extractor.py**

Create `django_apps/game_data/importers/custom_data_extractor.py`:

```python
"""Extract physics/rate parameters from building_variants.json CustomData.All[].

CustomData.All[] is a list of dicts. Each dict has one or more top-level keys
that identify a specific interface (e.g. "IConveyorConfiguration"). We parse
each known interface and emit RateParam rows for storage in BuildingVariantRateConfig.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RateParam:
    """One scalar parameter extracted from a CustomData interface."""

    interface_key: str
    param_key: str
    int_value: int | None = None
    float_value: float | None = None
    text_value: str = ""
    research_scale_id: str = ""


def _dig(data: Any, *keys: str, default: Any = None) -> Any:
    """Safe nested dict traversal."""
    for k in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(k, default)
    return data


def _extract_conveyor(iface_data: dict[str, Any]) -> list[RateParam]:
    speed = iface_data.get("ConveyorSpeed") or {}
    rows: list[RateParam] = []
    steps_raw = _dig(speed, "StepsPerTick", "Value", default=None)
    if steps_raw is not None:
        research = str(_dig(speed, "ResearchId", "Id", default="") or "")
        rows.append(RateParam(
            interface_key="IConveyorConfiguration",
            param_key="steps_per_tick",
            int_value=int(steps_raw),
            research_scale_id=research,
        ))
    base = speed.get("BaseSpeed")
    if base is not None:
        rows.append(RateParam(
            interface_key="IConveyorConfiguration",
            param_key="base_speed",
            float_value=float(base),
        ))
    return rows


def _extract_fluid_receiver(iface_data: dict[str, Any]) -> list[RateParam]:
    rate = _dig(
        iface_data,
        "ProvidingConfiguration",
        "IProvidingFluidContainerConfiguration",
        "ProvidingRate",
        "Value",
        default=None,
    )
    if rate is None:
        return []
    return [RateParam(
        interface_key="IFluidPortReceiverConfiguration",
        param_key="fluid_provide_rate",
        float_value=float(rate),
    )]


def _extract_fluid_sender(iface_data: dict[str, Any]) -> list[RateParam]:
    rate = _dig(
        iface_data,
        "ConsumingConfiguration",
        "IConsumingFluidContainerConfiguration",
        "ConsumingRate",
        "Value",
        default=None,
    )
    if rate is None:
        return []
    return [RateParam(
        interface_key="IFluidPortSenderConfiguration",
        param_key="fluid_consume_rate",
        float_value=float(rate),
    )]


def _extract_crystal_gen(iface_data: dict[str, Any]) -> list[RateParam]:
    rate = _dig(
        iface_data,
        "ContainerConfig",
        "IConsumingFluidContainerConfiguration",
        "ConsumingRate",
        "Value",
        default=None,
    )
    if rate is None:
        return []
    return [RateParam(
        interface_key="ICrystalGeneratorConfiguration",
        param_key="crystal_consume_rate",
        float_value=float(rate),
    )]


def _extract_fluid_storage(iface_data: dict[str, Any]) -> list[RateParam]:
    rows: list[RateParam] = []
    provide = _dig(
        iface_data,
        "ContainerConfig",
        "IProvidingFluidContainerConfiguration",
        "ProvidingRate",
        "Value",
        default=None,
    )
    if provide is not None:
        rows.append(RateParam(
            interface_key="IFluidStorageConfiguration",
            param_key="fluid_storage_provide_rate",
            float_value=float(provide),
        ))
    consume = _dig(
        iface_data,
        "ContainerConfig",
        "IConsumingFluidContainerConfiguration",
        "ConsumingRate",
        "Value",
        default=None,
    )
    if consume is not None:
        rows.append(RateParam(
            interface_key="IFluidStorageConfiguration",
            param_key="fluid_storage_consume_rate",
            float_value=float(consume),
        ))
    return rows


def _extract_pipe_gate(iface_data: dict[str, Any]) -> list[RateParam]:
    rows: list[RateParam] = []
    provide = _dig(
        iface_data,
        "ContainerConfig",
        "IProvidingFluidContainerConfiguration",
        "ProvidingRate",
        "Value",
        default=None,
    )
    if provide is not None:
        rows.append(RateParam(
            interface_key="IPipeGateConfiguration",
            param_key="pipe_gate_provide_rate",
            float_value=float(provide),
        ))
    consume = _dig(
        iface_data,
        "ContainerConfig",
        "IConsumingFluidContainerConfiguration",
        "ConsumingRate",
        "Value",
        default=None,
    )
    if consume is not None:
        rows.append(RateParam(
            interface_key="IPipeGateConfiguration",
            param_key="pipe_gate_consume_rate",
            float_value=float(consume),
        ))
    return rows


_INTERFACE_EXTRACTORS: dict[str, Any] = {
    "IConveyorConfiguration": _extract_conveyor,
    "IFluidPortReceiverConfiguration": _extract_fluid_receiver,
    "IFluidPortSenderConfiguration": _extract_fluid_sender,
    "ICrystalGeneratorConfiguration": _extract_crystal_gen,
    "IFluidStorageConfiguration": _extract_fluid_storage,
    "IPipeGateConfiguration": _extract_pipe_gate,
}


def extract_rate_params(definition_snapshot: dict[str, Any]) -> list[RateParam]:
    """Parse all known interface rate params from a building_variants.json row snapshot.

    Returns a flat list of RateParam; empty list if no known interfaces found.
    """
    all_items: list[Any] = (
        _dig(definition_snapshot, "IEntityDefinition", "CustomData", "All", default=[]) or []
    )
    results: list[RateParam] = []
    for item in all_items:
        if not isinstance(item, dict):
            continue
        for iface_key, extractor in _INTERFACE_EXTRACTORS.items():
            iface_data = item.get(iface_key)
            if iface_data is not None and isinstance(iface_data, dict):
                results.extend(extractor(iface_data))
    return results
```

- [ ] **Step 4: Confirm unit tests pass (no DB)

```bash
python -m pytest tests/unit/game_data/test_building_variant_rate_config.py -v -k "not django_db"
```
Expected: 10 tests PASS

- [ ] **Step 5: ruff + mypy**

```bash
python -m ruff check django_apps/game_data/importers/custom_data_extractor.py
python -m mypy django_apps/game_data/importers/custom_data_extractor.py
```
Expected: no errors

- [ ] **Step 6: commit**

```bash
git add django_apps/game_data/importers/custom_data_extractor.py tests/unit/game_data/test_building_variant_rate_config.py
git commit -m "feat(game_data): add CustomData.All[] rate param extractor with unit tests"
```

---

## Task 6: Wire importer — store BuildingVariantRateConfig

**Files:**
- Modify: `django_apps/game_data/importers/importer.py`
- Test: `tests/unit/game_data/test_building_variant_rate_config.py` (add DB tests)

- [ ] **Step 1: Add DB test (verify importer wiring)

Add at end of `tests/unit/game_data/test_building_variant_rate_config.py`:

```python
# ---------------------------------------------------------------------------
# DB integration tests — importer wiring
# ---------------------------------------------------------------------------

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.custom_data_extractor import extract_rate_params
from django_apps.game_data.models import BuildingVariant, BuildingVariantRateConfig, ImportBatch, SourceObject
from django_apps.game_data.services import identifiers


def _make_import_batch(suffix: str) -> ImportBatch:
    return ImportBatch.objects.create(
        manifest_self_hash=f"hash-rate-{suffix}",
        batch_name="test",
        game_version="1.0",
    )


def _make_variant(batch: ImportBatch, name: str) -> BuildingVariant:
    cid = identifiers.canonical_building_variant(name)
    return BuildingVariant.objects.create(
        canonical_id=cid,
        import_batch=batch,
        internal_name=name,
        source_stable_id="stb",
        source_row_index=0,
    )


@pytest.mark.django_db
def test_rate_config_created_for_conveyor_variant(db: None) -> None:
    batch = _make_import_batch("conv")
    variant = _make_variant(batch, "BeltVariantTest")
    snap = {
        "IEntityDefinition": {
            "CustomData": {
                "All": [
                    {
                        "IConveyorConfiguration": {
                            "ConveyorSpeed": {
                                "StepsPerTick": {"Value": 3},
                                "BaseSpeed": 2.0,
                                "ResearchId": {"Id": "UpgradeBelt"},
                            }
                        }
                    }
                ]
            }
        }
    }
    params = extract_rate_params(snap)
    cid_base = identifiers.canonical_building_variant("BeltVariantTest")
    for p in params:
        cid = identifiers.canonical_variant_rate_config(
            cid_base, p.interface_key, p.param_key
        )
        BuildingVariantRateConfig.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "variant": variant,
                "interface_key": p.interface_key,
                "param_key": p.param_key,
                "int_value": p.int_value,
                "float_value": p.float_value,
                "text_value": p.text_value,
                "research_scale_id": p.research_scale_id,
            },
        )

    steps = BuildingVariantRateConfig.objects.get(
        variant=variant,
        interface_key="IConveyorConfiguration",
        param_key="steps_per_tick",
    )
    assert steps.int_value == 3
    assert steps.research_scale_id == "UpgradeBelt"

    base = BuildingVariantRateConfig.objects.get(
        variant=variant,
        interface_key="IConveyorConfiguration",
        param_key="base_speed",
    )
    assert abs(base.float_value - 2.0) < 1e-6


@pytest.mark.django_db
def test_rate_config_empty_for_variant_without_custom_data(db: None) -> None:
    batch = _make_import_batch("empty")
    variant = _make_variant(batch, "PlainVariantTest")
    params = extract_rate_params({})
    assert params == []
    assert BuildingVariantRateConfig.objects.filter(variant=variant).count() == 0
```

- [ ] **Step 2: Confirm test failure (importer not wired yet)**

```bash
python -m pytest tests/unit/game_data/test_building_variant_rate_config.py::test_rate_config_created_for_conveyor_variant -v
```
Expected: this test may PASS via direct wiring — importer connection test in next Step

- [ ] **Step 3: importer.py — add `BuildingVariantRateConfig` import**

Add at top of `django_apps/game_data/importers/importer.py` imports:

```python
from django_apps.game_data.importers.custom_data_extractor import extract_rate_params
# ... add to existing model imports:
from django_apps.game_data.models import (
    ...
    BuildingVariantRateConfig,   # NEW
    ...
)
```

- [ ] **Step 4: importer.py — add rate config storage at end of `_import_building_variants`**

Add just before `self.ctx.bump("building_variant")` in `_import_building_variants` method:

```python
# Phase 3: CustomData.All[] rate params
snap_for_rates = row.get("definition_snapshot") or {}
params = extract_rate_params(snap_for_rates)
BuildingVariantRateConfig.objects.filter(variant=variant).delete()
rate_count = 0
for p in params:
    rate_cid = identifiers.canonical_variant_rate_config(
        cid, p.interface_key, p.param_key
    )
    BuildingVariantRateConfig.objects.create(
        canonical_id=rate_cid,
        variant=variant,
        interface_key=p.interface_key,
        param_key=p.param_key,
        int_value=p.int_value,
        float_value=p.float_value,
        text_value=p.text_value,
        research_scale_id=p.research_scale_id,
    )
    rate_count += 1
if rate_count:
    self.ctx.bump("building_variant_rate_config", rate_count)
```

Full `_import_building_variants` method (after change):

```python
def _import_building_variants(self) -> None:
    assert self.ctx is not None
    rows = load_json(self._path("building_variants.json"))
    for i, row in enumerate(rows):
        snap = row.get("definition_snapshot") or {}
        internal = str(dig(snap, "Id", "Name", default=""))
        if not internal:
            continue
        cid = identifiers.canonical_building_variant(internal)
        src = self._source_object("building_variants.json", i, row)
        variant, _ = BuildingVariant.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": self.ctx.batch,
                "internal_name": internal,
                "source_stable_id": str(row.get("stable_id", "")),
                "display_name_key": str(row.get("display_name_key", "")),
                "is_mirrored": internal.endswith("Mirrored"),
                "size_x": int(
                    dig(snap, "ConnectorData", "TileDimensions", "x", default=0) or 0
                ),
                "size_y": int(
                    dig(snap, "ConnectorData", "TileDimensions", "y", default=0) or 0
                ),
                "size_z": int(
                    dig(snap, "ConnectorData", "TileDimensions", "z", default=0) or 0
                ),
                "source_row_index": i,
                "source_object": src,
            },
        )
        connectors = dig(snap, "ConnectorData", "AllBuildingConnectors", default=[]) or []
        variant.connector_count = len(connectors)
        variant.save(update_fields=["connector_count"])
        BuildingConnector.objects.filter(building_variant=variant).delete()
        for oi, conn in enumerate(connectors):
            role = str(conn.get("$type", "unknown")).rsplit(".", maxsplit=1)[-1]
            pos = conn.get("Position_L") or {}
            BuildingConnector.objects.create(
                canonical_id=identifiers.canonical_connector(cid, oi),
                building_variant=variant,
                order_index=oi,
                connector_role=role[:64],
                tile_direction=str(dig(conn, "TileDirection", "Value", default="")),
                io_channel_type=str(conn.get("IOType", "")),
                has_seperators=bool(conn.get("Seperators")),
                position_x=int(pos.get("x", 0) or 0),
                position_y=int(pos.get("y", 0) or 0),
                position_z=int(pos.get("z", 0) or 0),
            )
        BuildingFootprintTile.objects.filter(building_variant=variant).delete()
        for oi, tile in enumerate(dig(snap, "ConnectorData", "Tiles", default=[]) or []):
            BuildingFootprintTile.objects.create(
                canonical_id=identifiers.canonical_footprint_tile(cid, oi),
                building_variant=variant,
                order_index=oi,
                x=int(tile.get("x", 0) or 0),
                y=int(tile.get("y", 0) or 0),
                z=int(tile.get("z", 0) or 0),
            )
        # Phase 3: CustomData.All[] rate params
        params = extract_rate_params(snap)
        BuildingVariantRateConfig.objects.filter(variant=variant).delete()
        rate_count = 0
        for p in params:
            rate_cid = identifiers.canonical_variant_rate_config(
                cid, p.interface_key, p.param_key
            )
            BuildingVariantRateConfig.objects.create(
                canonical_id=rate_cid,
                variant=variant,
                interface_key=p.interface_key,
                param_key=p.param_key,
                int_value=p.int_value,
                float_value=p.float_value,
                text_value=p.text_value,
                research_scale_id=p.research_scale_id,
            )
            rate_count += 1
        if rate_count:
            self.ctx.bump("building_variant_rate_config", rate_count)
        self.ctx.bump("building_variant")
```

- [ ] **Step 5: Confirm all tests pass**

```bash
python -m pytest tests/unit/game_data/test_building_variant_rate_config.py -v
```
Expected: PASS (all tests)

- [ ] **Step 6: ruff + mypy**

```bash
python -m ruff check django_apps/game_data/importers/importer.py
python -m mypy django_apps/game_data/importers/importer.py
```
Expected: no errors

- [ ] **Step 7: commit**

```bash
git add django_apps/game_data/importers/importer.py tests/unit/game_data/test_building_variant_rate_config.py
git commit -m "feat(game_data): wire CustomData rate extractor into building variant importer"
```

---

## Task 7: Coverage Manifest registration

**Files:**
- Modify: `django_apps/game_data/coverage/manifest.py`
- Modify: `tests/unit/game_data/test_domain_coverage_manifest.py`

- [ ] **Step 1: Add Phase 3 entries to manifest.py**

Full `django_apps/game_data/coverage/manifest.py` (after update):

```python
"""Static path disposition registry (A1 coverage manifest)."""

from __future__ import annotations

from django_apps.game_data.coverage import reason_codes as rc
from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.simulation_paths import manifest_entries_from_rules

MANIFEST: dict[str, tuple[Disposition, str]] = {
    "items.json:definition_snapshot.Definition.Layers": (
        Disposition.PROMOTED,
        "ShapeRecipe tree",
    ),
    "items.json:catalog": (
        Disposition.CROSS_REF,
        "ShapeRecipeSourceAppearance",
    ),
    "shapes.json:definition_snapshot.Definition": (
        Disposition.PROMOTED,
        "ShapeRecipe + FULL appearance",
    ),
    "toolbar_entries.json:display_name_key": (
        Disposition.PROMOTED,
        "ToolbarTreeNode.tree_path",
    ),
    "toolbar_entries.json:Children": (
        Disposition.CROSS_REF,
        "flattened to row paths",
    ),
    "simulation_systems.json:ISimulationSystem": (
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    "simulation_systems.json:SimulationFactory": (
        Disposition.IGNORE_AUDIT,
        rc.SIMULATION_FACTORY_STUB,
    ),
    "buildings.json:definition_snapshot.Assembly": (
        Disposition.IGNORE_AUDIT,
        rc.REFLECTION_METADATA,
    ),
    "buildings.json:PlacementRequirements": (
        Disposition.PROMOTED,
        "BuildingPlacementRule",
    ),
    "buildings.json:Definitions": (
        Disposition.PROMOTED,
        "BuildingGroupMember",
    ),
    # Phase 3: buildings.json — DLC and reward flags
    "buildings.json:RequiredStoreContentId": (
        Disposition.PROMOTED,
        "BuildingGroup.required_store_content_id",
    ),
    "buildings.json:ShowAsResearchReward": (
        Disposition.PROMOTED,
        "BuildingGroup.show_as_research_reward",
    ),
    # Phase 3: building_variants.json — CustomData rate params (promoted)
    "building_variants.json:IEntityDefinition.CustomData.All[].IConveyorConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidStorageConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].IPipeGateConfiguration": (
        Disposition.PROMOTED,
        "BuildingVariantRateConfig",
    ),
    # Phase 3: building_variants.json — ignore paths
    "building_variants.json:ConnectorData.TileBounds": (
        Disposition.IGNORE_AUDIT,
        rc.LAYOUT_METADATA,
    ),
    "building_variants.json:ConnectorData.AllBuildingConnectors[]._IOType": (
        Disposition.IGNORE_AUDIT,
        rc.LEGACY_FIELD,
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].CustomDrawData": (
        Disposition.IGNORE_AUDIT,
        rc.RENDER_METADATA,
    ),
    "building_variants.json:IEntityDefinition.CustomData.All[].Definitions[]": (
        Disposition.IGNORE_AUDIT,
        rc.NESTED_ENTITY_DEF,
    ),
    "building_variants.json:IEntityDefinition.CustomData.DataPerTypeCache": (
        Disposition.IGNORE_AUDIT,
        rc.REFLECTION_CACHE,
    ),
}
MANIFEST.update(manifest_entries_from_rules())
```

- [ ] **Step 2: Confirm existing manifest tests pass (regression)

```bash
python -m pytest tests/unit/game_data/test_domain_coverage_manifest.py -v
```
Expected: PASS (2 existing tests)

- [ ] **Step 3: Add Phase 3 manifest key verification test**

Add at end of `tests/unit/game_data/test_domain_coverage_manifest.py`:

```python
import pytest
from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.manifest import MANIFEST


_PHASE3_PROMOTED_KEYS = [
    "buildings.json:RequiredStoreContentId",
    "buildings.json:ShowAsResearchReward",
    "building_variants.json:IEntityDefinition.CustomData.All[].IConveyorConfiguration",
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration",
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration",
    "building_variants.json:IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration",
    "building_variants.json:IEntityDefinition.CustomData.All[].IFluidStorageConfiguration",
    "building_variants.json:IEntityDefinition.CustomData.All[].IPipeGateConfiguration",
]

_PHASE3_IGNORE_KEYS = [
    "building_variants.json:ConnectorData.TileBounds",
    "building_variants.json:ConnectorData.AllBuildingConnectors[]._IOType",
    "building_variants.json:IEntityDefinition.CustomData.All[].CustomDrawData",
    "building_variants.json:IEntityDefinition.CustomData.All[].Definitions[]",
    "building_variants.json:IEntityDefinition.CustomData.DataPerTypeCache",
]


@pytest.mark.parametrize("key", _PHASE3_PROMOTED_KEYS)
def test_phase3_promoted_key_in_manifest(key: str) -> None:
    assert key in MANIFEST
    disposition, note = MANIFEST[key]
    assert disposition == Disposition.PROMOTED
    assert note.strip()


@pytest.mark.parametrize("key", _PHASE3_IGNORE_KEYS)
def test_phase3_ignore_audit_key_in_manifest(key: str) -> None:
    assert key in MANIFEST
    disposition, note = MANIFEST[key]
    assert disposition == Disposition.IGNORE_AUDIT
    assert note.strip()
```

- [ ] **Step 4: All manifest tests pass including new tests

```bash
python -m pytest tests/unit/game_data/test_domain_coverage_manifest.py -v
```
Expected: PASS (2 existing + 13 new = 15 tests)

- [ ] **Step 5: commit**

```bash
git add django_apps/game_data/coverage/manifest.py tests/unit/game_data/test_domain_coverage_manifest.py
git commit -m "feat(game_data): register Phase 3 promoted/ignore_audit paths in coverage manifest"
```

---

## Task 8: Regression verification + reimport

- [ ] **Step 1: Full pytest**

```bash
python -m pytest tests/ -v --tb=short
```
Expected: all existing tests PASS + new tests PASS

- [ ] **Step 2: ruff + mypy + black**

```bash
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```
Expected: no errors

- [ ] **Step 3: SQLite reimport + update dumpdata

```bash
$env:DJANGO_USE_SQLITE = "1"
python manage.py migrate game_data
python manage.py flush --no-input
python manage.py import_game_data --source documents/game_data
python manage.py dumpdata game_data --indent 2 -o game_data_backup/game_data_dump.json
```

Expected: import complete, `building_variant_rate_config` count > 0 output

- [ ] **Step 4: verify import**

```bash
python manage.py import_game_data --verify
```
Expected: no errors

- [ ] **Step 5: Final commit**

```bash
git add game_data_backup/game_data_dump.json
git commit -m "chore(game_data): regenerate dumpdata after Phase 3 gap fill migration"
```

---

## Self-Review Checklist

| Spec requirement | Implementation Task |
|---|---|
| `BuildingVariantRateConfig` new model (no JSONField) | Task 4 |
| `BuildingGroup.required_store_content_id` | Task 3 |
| `BuildingGroup.show_as_research_reward` | Task 3 |
| `FluidColor.display_name_key` | Task 2 |
| 5 new reason_codes | Task 1 |
| manifest 6 PROMOTED + 5 IGNORE_AUDIT registrations | Task 7 |
| conveyor steps_per_tick extraction | Task 5 |
| conveyor base_speed extraction | Task 5 |
| conveyor research_scale_id extraction | Task 5 |
| fluid receiver provide_rate extraction | Task 5 |
| fluid sender consume_rate extraction | Task 5 |
| crystal generator consume_rate extraction | Task 5 |
| fluid storage provide/consume rate extraction | Task 5 |
| pipe gate provide/consume rate extraction | Task 5 |
| `ctx.record_unknown` — parse failure record | (extract_rate_params skips silently; extend in Task 6 if needed) |
| migration + dumpdata | Task 4 + Task 8 |
| regression: `test_simulation_path_coverage.py` | Task 8 |

**Placeholder check:** No TBD/TODO. All code blocks complete.

**Type consistency:** `RateParam` defined in Task 5, used in Task 6. Field names `int_value`, `float_value`, `text_value`, `research_scale_id` consistent.
