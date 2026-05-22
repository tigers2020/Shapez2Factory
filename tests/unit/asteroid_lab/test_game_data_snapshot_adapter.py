"""Transport adapter for game_data snapshot strings."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.game_data_snapshot_adapter import (
    map_io_channel_to_transport_kind,
)
from django_apps.asteroid_lab.optimization.enums import TransportKind


@pytest.mark.parametrize(
    ("io_channel", "expected"),
    [
        ("Shape", TransportKind.SHAPE_BELT),
        ("Fluid", TransportKind.FLUID_PIPE),
    ],
)
def test_known_io_channel_maps(io_channel: str, expected: TransportKind) -> None:
    assert map_io_channel_to_transport_kind(io_channel) is expected


def test_unknown_io_channel_raises() -> None:
    with pytest.raises(ValueError, match="unknown io_channel_type"):
        map_io_channel_to_transport_kind("Paint")
