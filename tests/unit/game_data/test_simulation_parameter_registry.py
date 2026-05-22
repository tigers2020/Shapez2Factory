"""SimulationSystemParameterKey + occurrence registry (no param values)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.db import models

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.simulation_systems import import_simulation_systems
from django_apps.game_data.models import (
    ImportBatch,
    SimulationSystem,
    SimulationSystemParameterKey,
    SimulationSystemParameterOccurrence,
    UnknownProperty,
)
from django_apps.game_data.services.simulation_parameter_classify import (
    REASON_SIM_PARAM_REFLECTION_DUMP,
    ParameterClassification,
    classify_simulation_parameter_key,
)


@pytest.fixture
def min_sim_rows() -> list[dict]:
    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "game_data"
        / "simulation_systems_min.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def sim_batch() -> ImportBatch:
    return ImportBatch.objects.create(
        batch_name="sim-param-registry",
        manifest_self_hash="sha256:sim-param-registry",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )


def test_classify_known_keys() -> None:
    assert (
        classify_simulation_parameter_key("SimulationFactory")
        == ParameterClassification.DOMAIN_CONFIG
    )
    assert (
        classify_simulation_parameter_key("OnSimulationCreated")
        == ParameterClassification.EVENT_DELEGATE
    )
    assert (
        classify_simulation_parameter_key("ISimulationSystem.OnSimulationCreated")
        == ParameterClassification.REFLECTION_DUMP
    )
    assert (
        classify_simulation_parameter_key("ReceivedShapes") == ParameterClassification.RUNTIME_STATE
    )


@pytest.mark.django_db
def test_import_records_parameter_occurrences_without_values(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    import_simulation_systems(ImportContext(sim_batch), min_sim_rows)

    factory = SimulationSystem.objects.get(
        import_batch=sim_batch, source_stable_id="min-factory-001"
    )
    factory_keys = set(
        SimulationSystemParameterOccurrence.objects.filter(simulation_system=factory).values_list(
            "parameter_key__name",
            flat=True,
        )
    )
    assert factory_keys == {"SimulationFactory"}

    factory_occ = SimulationSystemParameterOccurrence.objects.get(
        simulation_system=factory,
        parameter_key__name="SimulationFactory",
    )
    assert factory_occ.source_path == "simulation_parameters.SimulationFactory"
    for field in SimulationSystemParameterOccurrence._meta.fields:
        assert not isinstance(field, models.JSONField)
        assert "value" not in field.name.lower()

    converter = SimulationSystem.objects.get(
        import_batch=sim_batch, source_stable_id="min-converter-003"
    )
    delegate_occ = SimulationSystemParameterOccurrence.objects.get(
        simulation_system=converter,
        parameter_key__name="ISimulationSystem.OnSimulationCreated",
    )
    assert delegate_occ.parameter_key.classification == ParameterClassification.REFLECTION_DUMP

    sim_key = SimulationSystemParameterKey.objects.get(name="SimulationFactory")
    assert sim_key.occurrence_count == 1


@pytest.mark.django_db
def test_reimport_does_not_inflate_occurrence_count(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    ctx = ImportContext(sim_batch)
    import_simulation_systems(ctx, min_sim_rows[:1])
    import_simulation_systems(ctx, min_sim_rows[:1])

    key = SimulationSystemParameterKey.objects.get(name="SimulationFactory")
    assert key.occurrence_count == 1
    assert SimulationSystemParameterOccurrence.objects.filter(parameter_key=key).count() == 1


@pytest.mark.django_db
def test_connectable_row_registers_domain_config_key(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    import_simulation_systems(ImportContext(sim_batch), [min_sim_rows[1]])

    system = SimulationSystem.objects.get(
        import_batch=sim_batch, source_stable_id="min-connectable-002"
    )
    param_key = SimulationSystemParameterKey.objects.get(name="ConnectableSimulations")
    assert param_key.classification == ParameterClassification.DOMAIN_CONFIG
    assert SimulationSystemParameterOccurrence.objects.filter(
        simulation_system=system,
        parameter_key=param_key,
    ).exists()


@pytest.mark.django_db
def test_converter_records_reflection_delegate_as_unknown_property(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    import_simulation_systems(ImportContext(sim_batch), [min_sim_rows[2]])

    ignored = UnknownProperty.objects.filter(
        import_batch=sim_batch,
        owner_model="SimulationSystem",
        owner_key="min-converter-003",
    )
    assert set(ignored.values_list("key", flat=True)) == {
        "ISimulationSystem.OnSimulationCreated",
        "Simulations",
    }
    reflection = ignored.filter(key="ISimulationSystem.OnSimulationCreated").first()
    assert reflection is not None
    assert reflection.reason_code == REASON_SIM_PARAM_REFLECTION_DUMP
    assert reflection.classification == ParameterClassification.REFLECTION_DUMP
    assert reflection.json_path == "simulation_parameters.ISimulationSystem.OnSimulationCreated"
    assert "audit-only" in reflection.value_preview


@pytest.mark.django_db
def test_factory_row_does_not_record_domain_config_as_unknown(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    import_simulation_systems(ImportContext(sim_batch), [min_sim_rows[0]])

    assert not UnknownProperty.objects.filter(
        import_batch=sim_batch,
        owner_key="min-factory-001",
        key="SimulationFactory",
    ).exists()


@pytest.mark.django_db
def test_reimport_ignored_simulation_parameter_is_idempotent(
    min_sim_rows: list[dict],
    sim_batch: ImportBatch,
) -> None:
    ctx = ImportContext(sim_batch)
    import_simulation_systems(ctx, [min_sim_rows[2]])
    import_simulation_systems(ctx, [min_sim_rows[2]])

    assert (
        UnknownProperty.objects.filter(
            import_batch=sim_batch,
            owner_key="min-converter-003",
            reason_code=REASON_SIM_PARAM_REFLECTION_DUMP,
        ).count()
        == 1
    )
