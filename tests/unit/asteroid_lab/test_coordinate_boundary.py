"""Raw/import coordinate boundary contracts."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.server_coords import raw_x_to_dense_x


def test_raw_x_zero_maps_to_dense_index_zero() -> None:
    """Omitted / explicit ``X == 0`` uses dense column 0 (see server_coords)."""

    assert raw_x_to_dense_x(0) == 0
