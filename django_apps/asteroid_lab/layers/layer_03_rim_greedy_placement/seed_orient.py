"""Void-normal seed layout for rim greedy placement."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.rim_greedy import RimGreedyRejectReason
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_DIR_DELTA: dict[str, tuple[int, int]] = {
    "N": (0, 1),
    "E": (1, 0),
    "S": (0, -1),
    "W": (-1, 0),
}
_OUTPUT_TO_ROTATION: dict[str, int] = {"E": 0, "S": 1, "W": 2, "N": 3}


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
    "str_output_dir_to_direction",
]
