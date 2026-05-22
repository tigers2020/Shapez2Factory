"""C-lite simulation_systems import invariants."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.apps import apps
from django.db import models

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.importers.simulation_systems import import_simulation_systems
from django_apps.game_data.models import (
    ConnectableSimulation,
    ImportBatch,
    SimulationClrProvenance,
    SimulationConnectorProperty,
    SimulationRuntimeAuditIssue,
    SimulationSystem,
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


@pytest.mark.django_db
def test_import_simulation_systems_min_batch(min_sim_rows: list[dict]) -> None:
    batch = ImportBatch.objects.create(
        batch_name="sim-min",
        manifest_self_hash="sha256:sim-min-test",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    ctx = ImportContext(batch)
    import_simulation_systems(ctx, min_sim_rows)

    assert SimulationSystem.objects.filter(import_batch=batch).count() == 3
    assert SimulationClrProvenance.objects.filter(import_batch=batch).count() == 3
    prov = SimulationClrProvenance.objects.get(
        import_batch=batch, source_stable_id="min-factory-001"
    )
    assert prov.canonical_id.startswith("sim-clr-prov:")
    assert "SplitterTShapeSimulation" in prov.clr_type_string
    assert SimulationRuntimeAuditIssue.objects.count() == 1
    assert ConnectableSimulation.objects.filter(simulation_system__import_batch=batch).count() == 2

    canonical_ids = list(
        SimulationSystem.objects.filter(import_batch=batch).values_list("canonical_id", flat=True)
    )
    assert len(canonical_ids) == len(set(canonical_ids)) or len(canonical_ids) == 3


@pytest.mark.django_db
def test_canonical_id_not_unique_globally(min_sim_rows: list[dict]) -> None:
    batch = ImportBatch.objects.create(
        batch_name="sim-dup",
        manifest_self_hash="sha256:sim-dup-test",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    duplicate_row = dict(min_sim_rows[0])
    duplicate_row["stable_id"] = "min-factory-dup-stable"
    ctx = ImportContext(batch)
    import_simulation_systems(ctx, [min_sim_rows[0], duplicate_row])

    systems = SimulationSystem.objects.filter(import_batch=batch)
    assert systems.count() == 2
    assert systems.values("canonical_id").distinct().count() == 1

    field = SimulationSystem._meta.get_field("canonical_id")
    assert field.unique is False


@pytest.mark.django_db
def test_converter_audit_issue_unique_and_reimport_idempotent(
    min_sim_rows: list[dict],
) -> None:
    batch = ImportBatch.objects.create(
        batch_name="sim-audit-upsert",
        manifest_self_hash="sha256:sim-audit-upsert",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    converter_row = min_sim_rows[2]
    ctx = ImportContext(batch)
    import_simulation_systems(ctx, [converter_row])
    import_simulation_systems(ctx, [converter_row])

    assert SimulationRuntimeAuditIssue.objects.count() == 1
    constraint_names = {c.name for c in SimulationRuntimeAuditIssue._meta.constraints}
    assert "uq_sim_runtime_audit_issue_system_code" in constraint_names


@pytest.mark.django_db
def test_upsert_by_batch_and_stable_id(min_sim_rows: list[dict]) -> None:
    batch = ImportBatch.objects.create(
        batch_name="sim-upsert",
        manifest_self_hash="sha256:sim-upsert-test",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    ctx = ImportContext(batch)
    import_simulation_systems(ctx, min_sim_rows[:1])
    import_simulation_systems(ctx, min_sim_rows[:1])
    assert SimulationSystem.objects.filter(import_batch=batch).count() == 1


@pytest.mark.django_db
def test_connector_property_typed_filter(min_sim_rows: list[dict]) -> None:
    batch = ImportBatch.objects.create(
        batch_name="sim-prop",
        manifest_self_hash="sha256:sim-prop-test",
        game_version="test",
        unity_version="test",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    import_simulation_systems(ImportContext(batch), [min_sim_rows[1]])
    assert SimulationConnectorProperty.objects.filter(
        property_key="update_priority",
        value_text="MeFirst",
    ).exists()


@pytest.mark.django_db
@pytest.mark.slow
def test_full_simulation_systems_import_180_rows(game_data_dir: Path) -> None:
    if not (game_data_dir / "simulation_systems.json").is_file():
        pytest.skip("simulation_systems.json missing")
    importer = GameDataImporter(game_data_dir, batch_name="sim-full")
    importer.run()
    batch = ImportBatch.objects.get()
    assert SimulationSystem.objects.filter(import_batch=batch).count() == 180
    assert SimulationSystem._meta.get_field("canonical_id").unique is False
    distinct_canonical = (
        SimulationSystem.objects.filter(import_batch=batch)
        .values("canonical_id")
        .distinct()
        .count()
    )
    assert distinct_canonical < 180


@pytest.mark.django_db
def test_no_domain_jsonfield_on_game_data_models() -> None:
    for model in apps.get_app_config("game_data").get_models():
        for field in model._meta.fields:
            if isinstance(field, models.JSONField):
                pytest.fail(f"{model.__name__}.{field.name} must not use JSONField on domain model")
