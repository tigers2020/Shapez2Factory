"""Typed simulation_parameters speed tables (Buffable / Multiple belt speed)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.simulation_systems import import_simulation_systems
from django_apps.game_data.models import (
    GlobalBeltSpeedPolicy,
    ImportBatch,
    SimulationBuffableSpeed,
    SimulationMultipleBeltSpeed,
    SimulationSystem,
)


@pytest.fixture
def speed_rows() -> list[dict]:
    return [
        {
            "stable_id": "min-belt-speed-001",
            "source_type_name": "TrashSimulationSystem",
            "display_name_key": "TrashSimulationSystem",
            "definition_snapshot": {},
            "simulation_parameters": {
                "BeltSpeed": {
                    "$type": "BuffableBeltSpeed",
                    "BaseSpeed": "OneSecondPerTile",
                    "ResearchId": {"Id": "BeltSpeed"},
                    "StepsPerTick": {"Value": 25200},
                },
            },
        },
        {
            "stable_id": "min-conveyor-jump-002",
            "source_type_name": "AtomicStatefulIslandSimulationSystem`2[[Game, Game]]",
            "display_name_key": "island",
            "definition_snapshot": {},
            "simulation_parameters": {
                "ConveyorSpeed": {
                    "$type": "BuffableBeltSpeed",
                    "BaseSpeed": "OneSecondPerTile",
                    "ResearchId": {"Id": "BeltSpeed"},
                    "StepsPerTick": {"Value": 25200},
                },
                "JumpSpeed": {
                    "$type": "MultipleBeltSpeed",
                    "BaseSpeed": {"$cycle": "BuffableBeltSpeed"},
                    "Multiplier": 4,
                    "StepsPerTick": {"Value": 100800},
                },
            },
        },
    ]


@pytest.fixture
def speed_batch() -> ImportBatch:
    return ImportBatch.objects.create(
        batch_name="sim-speed",
        manifest_self_hash="sha256:sim-speed-test",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )


@pytest.mark.django_db
def test_import_buffable_and_multiple_belt_speed(
    speed_rows: list[dict], speed_batch: ImportBatch
) -> None:
    import_simulation_systems(ImportContext(speed_batch), speed_rows)

    belt_system = SimulationSystem.objects.get(
        import_batch=speed_batch, source_stable_id="min-belt-speed-001"
    )
    buffable = SimulationBuffableSpeed.objects.get(
        simulation_system=belt_system, parameter_name="BeltSpeed"
    )
    assert buffable.dump_type == "BuffableBeltSpeed"
    assert buffable.base_speed == "OneSecondPerTile"
    assert buffable.steps_per_tick == 25200

    island = SimulationSystem.objects.get(
        import_batch=speed_batch, source_stable_id="min-conveyor-jump-002"
    )
    conveyor = SimulationBuffableSpeed.objects.get(
        simulation_system=island, parameter_name="ConveyorSpeed"
    )
    jump = SimulationMultipleBeltSpeed.objects.get(
        simulation_system=island, parameter_name="JumpSpeed"
    )
    assert jump.dump_type == "MultipleBeltSpeed"
    assert jump.cycle_ref_type == "BuffableBeltSpeed"
    assert jump.multiplier == 4
    assert jump.steps_per_tick == 100800
    assert jump.buffable_base_id == conveyor.pk

    assert GlobalBeltSpeedPolicy.objects.filter(import_batch=speed_batch).count() == 1


@pytest.mark.django_db
def test_reimport_speed_rows_idempotent(speed_rows: list[dict], speed_batch: ImportBatch) -> None:
    ctx = ImportContext(speed_batch)
    import_simulation_systems(ctx, speed_rows)
    import_simulation_systems(ctx, speed_rows)

    assert SimulationBuffableSpeed.objects.count() == 2
    assert SimulationMultipleBeltSpeed.objects.count() == 1
