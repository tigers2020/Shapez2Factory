"""Track D+ — catalog geometry transform tests."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
    build_pattern_library,
)


def test_expected_footprint_east_identity_at_anchor() -> None:
    cells = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    got = expected_footprint_coords(
        cells,
        anchor_coord=(5, 7),
        rotation=CardinalDirection.E,
    )
    assert got == frozenset({(5, 7), (6, 7)})


@pytest.mark.synthetic_lin_patterns
def test_catalog_geometry_transform_matches_pattern_library_east_rotation() -> None:
    patterns = build_pattern_library()
    pat = next(p for p in patterns if p.pattern_id == "lin_e_len2")
    cells = tuple(
        BuildingFootprintCell(x, y, i) for i, (x, y) in enumerate(sorted(pat.occupied_offsets))
    )
    expected = expected_footprint_coords(
        cells,
        anchor_coord=(0, 0),
        rotation=CardinalDirection.E,
    )
    assert expected == pat.occupied_offsets


def test_empty_footprint_raises_catalog_transform_error() -> None:
    with pytest.raises(CatalogTransformError, match="empty footprint_cells"):
        expected_footprint_coords(
            (),
            anchor_coord=(0, 0),
            rotation=CardinalDirection.E,
        )
