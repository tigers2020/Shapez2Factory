"""Django space transport catalog import from game_data JSON (PR-L4-1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.services.space_transport_catalog_import import (
    import_space_transport_catalog_from_game_data,
)
from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportTileCatalog,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RESEARCH = _REPO_ROOT / "documents" / "game_data" / "research_unlocks.json"
_SIMULATION = _REPO_ROOT / "documents" / "game_data" / "simulation_systems.json"
_HAS_GAME_DATA = _RESEARCH.is_file() and _SIMULATION.is_file()


@pytest.mark.skipif(not _HAS_GAME_DATA, reason="documents/game_data JSON not present")
def test_import_includes_space_belt_forward_with_simulation_key() -> None:
    payload = import_space_transport_catalog_from_game_data(
        research_unlocks_path=_RESEARCH,
        simulation_systems_path=_SIMULATION,
    )
    catalog = SpaceTransportTileCatalog.from_payload(payload)
    entry = catalog.lookup_tile_id("SpaceBelt_Forward")
    assert entry.transport_kind == "space_belt"
    assert entry.group_id == "SpaceBeltsGroup"
    assert entry.simulation_system_key is not None
    assert "SpaceConveyorSimulation" in entry.simulation_system_key
    assert entry.io_signature is not None
    resolved = catalog.lookup_io(
        transport_kind="space_belt",
        input_mask=(False, False, True, False),
        output_mask=(True, False, False, False),
    )
    assert resolved.tile_id == "SpaceBelt_Forward"


@pytest.mark.skipif(not _HAS_GAME_DATA, reason="documents/game_data JSON not present")
def test_import_enumerates_54_island_transport_tiles() -> None:
    payload = import_space_transport_catalog_from_game_data(
        research_unlocks_path=_RESEARCH,
        simulation_systems_path=_SIMULATION,
    )
    catalog = SpaceTransportTileCatalog.from_payload(payload)
    belt = [e for e in catalog.entries if e.tile_id.startswith("SpaceBelt_")]
    pipe = [e for e in catalog.entries if e.tile_id.startswith("SpacePipe_")]
    assert len(belt) == 27
    assert len(pipe) == 27


@pytest.mark.skipif(not _HAS_GAME_DATA, reason="documents/game_data JSON not present")
def test_lift_tiles_imported_without_io_signature() -> None:
    payload = import_space_transport_catalog_from_game_data(
        research_unlocks_path=_RESEARCH,
        simulation_systems_path=_SIMULATION,
    )
    catalog = SpaceTransportTileCatalog.from_payload(payload)
    lift = catalog.lookup_tile_id("SpaceBelt_Lift1DownForward")
    assert lift.routing_allowed is False
    assert lift.io_signature is None
