"""Space transport tile catalog snapshot (PR-L4-1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportCatalogInvalid,
    SpaceTransportTileCatalog,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab"
_FIXTURE = _FIXTURE_DIR / "space_transport_catalog_min.json"


@pytest.fixture
def sample_catalog_snapshot() -> SpaceTransportTileCatalog:
    return SpaceTransportTileCatalog.from_file(_FIXTURE)


def test_catalog_lookup_forward_west_to_east(
    sample_catalog_snapshot: SpaceTransportTileCatalog,
) -> None:
    entry = sample_catalog_snapshot.lookup_io(
        transport_kind="space_belt",
        input_mask=(False, False, True, False),
        output_mask=(True, False, False, False),
    )
    assert entry.tile_id == "SpaceBelt_Forward"
    assert entry.canonical_rotation == 0


def test_catalog_lookup_by_tile_id(sample_catalog_snapshot: SpaceTransportTileCatalog) -> None:
    entry = sample_catalog_snapshot.lookup_tile_id("SpacePipe_Forward")
    assert entry.transport_kind == "space_pipe"


def test_catalog_lookup_missing_io_raises(
    sample_catalog_snapshot: SpaceTransportTileCatalog,
) -> None:
    with pytest.raises(SpaceTransportCatalogInvalid, match="no catalog entry"):
        sample_catalog_snapshot.lookup_io(
            transport_kind="space_belt",
            input_mask=(True, False, False, False),
            output_mask=(False, True, False, False),
        )


def test_unsupported_schema_rejected() -> None:
    payload = SpaceTransportTileCatalog.from_file(_FIXTURE).to_payload()
    payload["schema_version"] = "space_transport_catalog_v999"
    with pytest.raises(SpaceTransportCatalogInvalid):
        SpaceTransportTileCatalog.from_payload(payload)
