"""Transport mapping from game_data ``io_channel_type`` to ``TransportKind``."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.game_data_snapshot_adapter import (
    map_io_channel_to_transport_kind,
)
from django_apps.asteroid_lab.optimization.enums import TransportKind

# Documented IOType values from game_data analysis + empty model default.
_KNOWN_IO_CHANNEL_CASES: tuple[tuple[str, TransportKind], ...] = (
    ("", TransportKind.NONE),
    ("Building", TransportKind.NONE),
    ("ElevatedBorder", TransportKind.SHAPE_BELT),
    ("None", TransportKind.NONE),
    ("Pipe", TransportKind.FLUID_PIPE),
    ("Regular", TransportKind.SHAPE_BELT),
    ("Wire", TransportKind.NONE),
)


@pytest.mark.parametrize(("channel", "expected"), _KNOWN_IO_CHANNEL_CASES)
def test_map_io_channel_to_transport_kind_known_values(
    channel: str,
    expected: TransportKind,
) -> None:
    assert map_io_channel_to_transport_kind(channel) is expected


def test_map_io_channel_unknown_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unknown io_channel_type"):
        map_io_channel_to_transport_kind("NotARealIOType")


@pytest.mark.django_db
def test_imported_db_io_channel_types_are_exhaustively_mapped(
    imported_game_data_batch,
) -> None:
    from django_apps.game_data.models import BuildingConnector

    distinct = sorted(set(BuildingConnector.objects.values_list("io_channel_type", flat=True)))
    assert distinct, "expected connectors after import"
    for channel in distinct:
        map_io_channel_to_transport_kind(channel)
