"""Shim: pure seed-layout symbols relocated to
shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient.

``placement_extension_rotation`` stays here because it depends on
``django_apps.asteroid_lab.snapshots.equipment_bundles.ports_compatible`` (game-data catalog,
Django-coupled) and is consumed only by Django replay + tests, not the greedy hot path.
"""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.cardinal_map import (  # noqa: E501
    direction_child_to_parent,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (  # noqa: E501
    SeedLayout,
    SeedLayoutReject,
    layout_seed_at_anchor,
    placement_output_rotation,
    str_output_dir_to_direction,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


def placement_extension_rotation(
    *,
    miner_coord: Coord,
    extension_coord: Coord,
    miner_rotation: int,
    extension_kind: str = "shape_miner_extension",
    miner_kind: str = "shape_miner",
) -> int:
    """Quarter-turn ``R`` so extension ports link to the parent miner (lab decode contract)."""

    dir_child_to_parent = direction_child_to_parent(extension_coord, miner_coord)
    if dir_child_to_parent is None:
        msg = "extension and miner are not 4-neighbors on the map grid"
        raise ValueError(msg)
    for rotation in range(4):
        if ports_compatible(
            extension_kind,
            rotation,
            miner_kind,
            miner_rotation,
            dir_child_to_parent,
        ):
            return rotation
    msg = "no extension rotation links extension to miner"
    raise ValueError(msg)


__all__ = [
    "SeedLayout",
    "SeedLayoutReject",
    "layout_seed_at_anchor",
    "placement_extension_rotation",
    "placement_output_rotation",
    "str_output_dir_to_direction",
]
