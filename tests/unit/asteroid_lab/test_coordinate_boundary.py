"""Raw/import coordinate boundary contracts."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.copy_json_coords import raw_x_to_export_column


def test_raw_x_zero_maps_to_export_column_zero() -> None:
    """Omitted / explicit ``X == 0`` uses export column 0."""

    assert raw_x_to_export_column(0) == 0
