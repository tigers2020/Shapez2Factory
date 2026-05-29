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
    """First route-search coordinate from miner output (v1: fixed-output offset only)."""
    steps = steps_from_canonical_e(output_dir)
    offset = rotate_offset(CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET, steps)
    return (anchor_coord[0] + offset[0], anchor_coord[1] + offset[1])


__all__ = ["derive_transport_entry_coord"]
