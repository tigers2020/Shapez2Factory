"""Raw/import coordinate boundary contracts."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.snapshots.server_coords import raw_x_to_dense_x


def test_raw_to_server_rejects_true_raw_x_zero_only_at_import_boundary() -> None:
    with pytest.raises(ValueError, match="no x == 0"):
        raw_x_to_dense_x(0)
