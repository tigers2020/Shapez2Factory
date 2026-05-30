"""Void-normal seed layout for rim greedy placement."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.rim_greedy import RimGreedyRejectReason
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.cardinal_map import (
    CARDINAL_DIR_DELTA,
    direction_child_to_parent,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_DIR_DELTA = CARDINAL_DIR_DELTA
_OUTPUT_TO_ROTATION: dict[str, int] = {"E": 0, "S": 1, "W": 2, "N": 3}


def placement_output_rotation(output_dir: str) -> int:
    return _OUTPUT_TO_ROTATION[output_dir]


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


@dataclass(frozen=True, slots=True)
class SeedLayout:
    seed_id: str
    anchor: Coord
    output_dir: str
    direction: Direction
    rotation: int
    miner_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    equipment_cells: frozenset[Coord]
    m_output_stub: Coord
    transport_stub_cells: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class SeedLayoutReject:
    reason: RimGreedyRejectReason
    detail: str


def str_output_dir_to_direction(output_dir: str) -> Direction:
    return Direction(output_dir.lower())


def layout_seed_at_anchor(
    *,
    seed_id: str,
    anchor: Coord,
    output_dir: str,
    complete_map: ReconstructionCompleteMap,
) -> SeedLayout | SeedLayoutReject:
    if output_dir not in _DIR_DELTA:
        return SeedLayoutReject(
            reason=RimGreedyRejectReason.NO_VOID_NORMAL,
            detail=f"invalid output_dir {output_dir!r}",
        )

    dx, dy = _DIR_DELTA[output_dir]
    miner_cells = frozenset({anchor})
    extension_coord = (anchor[0] - dx, anchor[1] - dy)
    extension_cells = frozenset({extension_coord})
    stub_coord = (anchor[0] + dx, anchor[1] + dy)
    transport_stub_cells = frozenset({stub_coord})
    equipment_cells = miner_cells | extension_cells
    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells

    if not equipment_cells <= field_cells:
        return SeedLayoutReject(
            reason=RimGreedyRejectReason.FOOTPRINT_OUT_OF_FIELD,
            detail="equipment not on field",
        )
    if stub_coord in field_cells:
        return SeedLayoutReject(
            reason=RimGreedyRejectReason.M_OUTPUT_BLOCKED,
            detail="stub not in exterior void",
        )
    if stub_coord not in external_void:
        return SeedLayoutReject(
            reason=RimGreedyRejectReason.M_OUTPUT_BLOCKED,
            detail="stub not in external_void",
        )
    if transport_stub_cells & equipment_cells:
        return SeedLayoutReject(
            reason=RimGreedyRejectReason.ORIENTATION_MISMATCH,
            detail="stub overlaps equipment",
        )

    return SeedLayout(
        seed_id=seed_id,
        anchor=anchor,
        output_dir=output_dir,
        direction=str_output_dir_to_direction(output_dir),
        rotation=_OUTPUT_TO_ROTATION[output_dir],
        miner_cells=miner_cells,
        extension_cells=extension_cells,
        equipment_cells=equipment_cells,
        m_output_stub=stub_coord,
        transport_stub_cells=transport_stub_cells,
    )


__all__ = [
    "SeedLayout",
    "SeedLayoutReject",
    "layout_seed_at_anchor",
    "placement_extension_rotation",
    "placement_output_rotation",
    "str_output_dir_to_direction",
]
