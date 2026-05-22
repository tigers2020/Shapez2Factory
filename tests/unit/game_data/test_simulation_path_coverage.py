"""Phase 2: simulation_systems.json nested path disposition parity."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.manifest import MANIFEST
from django_apps.game_data.coverage.reason_codes import RUNTIME_DELEGATE
from django_apps.game_data.coverage.simulation_paths import classify_norm_path
from django_apps.game_data.models import (
    ConnectableSimulation,
    ImportBatch,
    SimulationConnector,
    SimulationLaneDefinition,
    UnknownProperty,
)

_REPO = Path(__file__).resolve().parents[3]
_PRIORITY_TSV = (
    _REPO
    / "documents"
    / "game_data_analysis"
    / "simulation_systems"
    / "_nested_path_audit_priority.tsv"
)


def _priority_paths() -> list[str]:
    msg = "run: python scripts/audit_simulation_nested_paths.py --normalized --priority"
    assert _PRIORITY_TSV.is_file(), msg
    lines = _PRIORITY_TSV.read_text(encoding="utf-8-sig").strip().splitlines()[1:]
    return [ln.split("\t", 1)[0] for ln in lines if ln.strip() and not ln.startswith("#")]


@pytest.mark.parametrize("norm_path", _priority_paths())
def test_priority_audit_path_has_manifest_disposition(norm_path: str) -> None:
    key = f"simulation_systems.json:{norm_path}"
    assert key in MANIFEST or classify_norm_path(norm_path) is not None


def test_chain_positions_classified_ignore_audit() -> None:
    classified = classify_norm_path(
        "definition_snapshot.ISimulationSystem.OnSimulationCreated.Listeners[]."
        "Target.TileBasedSystems[].ChainPositions"
    )
    assert classified is not None
    assert classified[0] == Disposition.IGNORE_AUDIT
    assert classified[1] == RUNTIME_DELEGATE


def test_connectable_root_promoted_in_manifest() -> None:
    entry = MANIFEST["simulation_systems.json:simulation_parameters.ConnectableSimulations"]
    assert entry[0] == Disposition.PROMOTED


@pytest.mark.django_db
def test_connectable_profile_has_promoted_rows_not_only_unknown(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    assert ConnectableSimulation.objects.filter(simulation_system__import_batch=batch).exists()
    assert SimulationConnector.objects.filter(
        connectable_simulation__simulation_system__import_batch=batch
    ).exists()
    assert SimulationLaneDefinition.objects.filter(
        connectable_simulation__simulation_system__import_batch=batch
    ).exists()


@pytest.mark.django_db
def test_definition_snapshot_chain_positions_unknown_after_import(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    qs = UnknownProperty.objects.filter(
        import_batch=batch,
        owner_model="SimulationSystem",
        reason_code=RUNTIME_DELEGATE,
        json_path__contains="ChainPositions",
    )
    assert qs.exists()
