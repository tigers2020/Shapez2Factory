"""Track D+ PR-3 — catalog output attachment tests."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import expected_footprint_coords
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)


def _variant_east_chain() -> VariantGeometryCatalog:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (
        BuildingConnectorSnapshot(
            0,
            "output",
            "East",
            "Regular",
            1,
            0,
            0,
        ),
    )
    return VariantGeometryCatalog("bv:test", "test", footprint, connectors)


def test_attachment_east_expected_stub_from_fixture() -> None:
    geom = _variant_east_chain()
    att = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att is not None
    assert att.output_stub_offset == (2, 0)
    assert att.output_dir == "E"
    occupied = expected_footprint_coords(
        geom.footprint_cells,
        anchor_coord=(0, 0),
        rotation=CardinalDirection.E,
    )
    assert att.output_stub_offset not in occupied


def test_attachment_north_tile_direction_uses_project_coord_convention() -> None:
    geom = VariantGeometryCatalog(
        "bv:north",
        "north",
        (BuildingFootprintCell(0, 0, 0),),
        (
            BuildingConnectorSnapshot(
                0,
                "output",
                "North",
                "Regular",
                0,
                0,
                0,
            ),
        ),
    )
    att = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att is not None
    assert att.output_dir == "N"
    assert att.output_stub_offset == (0, -1)


def test_attachment_n_rotation_differs_from_east() -> None:
    geom = _variant_east_chain()
    att_n = attachment_for_variant_rotation(geom, CardinalDirection.N)
    att_e = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att_n is not None and att_e is not None
    assert att_n.output_dir == "N"
    assert att_n.output_stub_offset != att_e.output_stub_offset


def test_attachment_building_item_output_role() -> None:
    geom = VariantGeometryCatalog(
        "variant:BeltDefaultForwardInternalVariant",
        "belt",
        (BuildingFootprintCell(0, 0, 0),),
        (
            BuildingConnectorSnapshot(0, "BuildingItemInput", "West", "Regular", 0, 0, 0),
            BuildingConnectorSnapshot(1, "BuildingItemOutput", "East", "Regular", 0, 0, 0),
        ),
    )
    att = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att is not None
    assert att.output_dir == "E"
    assert att.output_stub_offset == (1, 0)


def test_attachment_none_when_no_output_connector() -> None:
    geom = VariantGeometryCatalog("bv:x", "x", (BuildingFootprintCell(0, 0, 0),), ())
    assert attachment_for_variant_rotation(geom, CardinalDirection.E) is None
