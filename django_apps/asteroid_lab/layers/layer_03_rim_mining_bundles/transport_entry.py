"""Derive L3 transport entry coordinate from rim anchor and output direction."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.coord_transform import (
    rotate_offset,
    steps_from_canonical_e,
)
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def derive_transport_entry_coord(
    *,
    anchor_coord: Coord,
    output_dir: Direction,
) -> Coord:
    """First route-search coordinate from miner output (v1: fixed-output offset only).

    ``output_dir`` is the physical exterior / miner-facing direction. The canonical
    gene stub at ``(1, 0)`` is on the field-input side at R=0, so N/S exterior
    voids need a 180° offset flip to land the transport cell on the void neighbor.
    """
    steps = steps_from_canonical_e(output_dir)
    if output_dir in (Direction.N, Direction.S):
        steps = (steps + 2) % 4
    offset = rotate_offset(CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET, steps)
    return (anchor_coord[0] + offset[0], anchor_coord[1] + offset[1])


__all__ = ["derive_transport_entry_coord"]
