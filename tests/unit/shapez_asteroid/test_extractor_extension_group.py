"""Parent-link extension ownership and maximized-group detection (blueprint-only path)."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    rotation_r_for_output_direction,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS12_MAX_EXTENSION_TILES,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extractor_extension_group import (  # noqa: E501
    extension_parent_coord,
    owned_extension_cells_for_extractor,
    route_extractor_is_maximized_group,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)


def _ext_row(r: int) -> dict:
    return {
        "role": "occupied",
        "surface": "shape",
        "layout_kind": "extension",
        "t": "Layout_ShapeMinerExtension",
        "r": r,
    }


def _miner_row(r: int) -> dict:
    return {
        "role": "occupied",
        "surface": "shape",
        "layout_kind": "miner",
        "t": "Layout_ShapeMiner",
        "r": r,
    }


def test_straight_three_extensions_owned_by_miner_maximized() -> None:
    # Core at (5,1), output east → stub (6,1); extensions west chain (4,1),(3,1),(2,1)
    r = rotation_r_for_output_direction(1, 0)
    east = rotation_r_for_output_direction(1, 0)
    cells: dict[Coord, dict] = {
        (5, 1): _miner_row(r),
        (4, 1): _ext_row(east),
        (3, 1): _ext_row(east),
        (2, 1): _ext_row(east),
    }
    owned = owned_extension_cells_for_extractor(cells, (5, 1))
    assert len(owned) == PASS12_MAX_EXTENSION_TILES
    assert route_extractor_is_maximized_group(
        extractor_cell=(5, 1),
        placement_id=None,
        placement_records=None,
        cells=cells,
    )


def test_cycle_extensions_not_owned() -> None:
    # A(1,1) faces B, B(2,1) faces A — neither reaches extractor at (3,1)
    cells: dict[Coord, dict] = {
        (3, 1): _miner_row(rotation_r_for_output_direction(1, 0)),
        (1, 1): _ext_row(rotation_r_for_output_direction(1, 0)),  # toward (2,1)
        (2, 1): _ext_row(rotation_r_for_output_direction(-1, 0)),  # toward (1,1)
    }
    assert owned_extension_cells_for_extractor(cells, (3, 1)) == frozenset()
    assert not route_extractor_is_maximized_group(
        extractor_cell=(3, 1),
        placement_id=None,
        placement_records=None,
        cells=cells,
    )


def test_missing_r_extension_unresolved() -> None:
    cells: dict[Coord, dict] = {
        (2, 1): _miner_row(rotation_r_for_output_direction(1, 0)),
        (1, 1): {"role": "occupied", "layout_kind": "extension", "surface": "shape"},
    }
    assert extension_parent_coord((1, 1), cells[(1, 1)]) is None
    assert owned_extension_cells_for_extractor(cells, (2, 1)) == frozenset()


def test_extension_pointing_at_other_miner_not_owned() -> None:
    r0 = rotation_r_for_output_direction(1, 0)
    r1 = rotation_r_for_output_direction(-1, 0)
    cells: dict[Coord, dict] = {
        (2, 1): _miner_row(r0),
        (4, 1): _miner_row(r1),
        (3, 1): _ext_row(rotation_r_for_output_direction(1, 0)),  # parent (4,1), not (2,1)
    }
    assert owned_extension_cells_for_extractor(cells, (2, 1)) == frozenset()


def test_placement_record_three_extensions_maximized_without_map_walk() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000001",
        placement_pass="pass1",
        extractor_cell=(5, 5),
        extension_cells=((4, 5), (3, 5), (2, 5)),
        stub_cell=(6, 5),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
    )
    cells: dict[Coord, dict] = {}
    assert route_extractor_is_maximized_group(
        extractor_cell=(5, 5),
        placement_id="p1-000001",
        placement_records={"p1-000001": rec},
        cells=cells,
    )
    rec2 = PlacementCommitRecord(
        placement_id="p1-000002",
        placement_pass="pass1",
        extractor_cell=(5, 5),
        extension_cells=((4, 5), (3, 5)),
        stub_cell=(6, 5),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
    )
    assert not route_extractor_is_maximized_group(
        extractor_cell=(5, 5),
        placement_id="p1-000002",
        placement_records={"p1-000002": rec2},
        cells=cells,
    )
