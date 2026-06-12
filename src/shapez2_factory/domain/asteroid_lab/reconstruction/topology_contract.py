"""Normalized reconstruction topology for fixture pair acceptance (raw island X/Y only).

Pure core: decode + topology set construction + diff helpers. Test-fixture file loaders live
in the Django module ``django_apps.asteroid_lab.reconstruction.topology_contract`` (they read
``tests/fixtures``), which re-exports these pure symbols.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string
from shapez2_factory.domain.asteroid_lab.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import BBox, Coord, bbox_from_coords
from shapez2_factory.domain.asteroid_lab.normalization import normalize_decoded_blueprint
from shapez2_factory.domain.asteroid_lab.reconstruction.acceptance_topology import (
    infer_topology_coord_frame,
    topology_coord_for_cell,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.grid import Coord as RawCoord
from shapez2_factory.domain.asteroid_lab.service_dtos import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
)

_DIFF_LIST_CAP = 50


@dataclass(frozen=True, slots=True)
class NormalizedReconstructionTopology:
    """Island-grid topology sets for compare (layer duplicates collapse to ``(x, y)``)."""

    mineable_cells: frozenset[Coord]
    wall_cells: frozenset[Coord]
    interior_patch_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    asteroid_cells: frozenset[Coord]
    bbox: BBox


def decode_shapez_copy_string(copy_string: str) -> DecodedBlueprintSnapshotDTO:
    """Decode + normalize + snapshot DTO."""

    norm = normalize_decoded_blueprint(decode_copy_string(copy_string.strip().removesuffix("$")))
    return build_decoded_blueprint_snapshot(norm.decoded_json)


def _is_mineable_occupied(cell: DecodedCellDTO) -> bool:
    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        return True
    return cell.cell_kind in MINER_EXTENSION_CELL_KINDS


def _shell_topology_coords(
    shell_raw_coords: frozenset[RawCoord] | None,
    *,
    coord_frame: CoordFrame,
) -> frozenset[Coord]:
    if not shell_raw_coords:
        return frozenset()
    if coord_frame == CoordFrame.ISLAND_RAW:
        return frozenset(shell_raw_coords)
    return frozenset()


def build_normalized_reconstruction_topology(
    cells: Sequence[DecodedCellDTO],
    *,
    shell_raw_coords: frozenset[RawCoord] | None = None,
    coord_frame: CoordFrame | None = None,
) -> NormalizedReconstructionTopology:
    """Build compare topology from decoded or reconstruction-merged cells."""

    frame = coord_frame if coord_frame is not None else infer_topology_coord_frame(cells)
    mineable: set[Coord] = set()
    wall: set[Coord] = set()
    occupied: set[Coord] = set()

    for cell in cells:
        try:
            sv = topology_coord_for_cell(cell, coord_frame=frame)
        except ValueError:
            continue
        occupied.add(sv)
        if _is_mineable_occupied(cell):
            mineable.add(sv)
        elif is_asteroid_evidence(cell):
            wall.add(sv)

    shell_sv = _shell_topology_coords(shell_raw_coords, coord_frame=frame)
    interior_patch = mineable - shell_sv if shell_sv else frozenset(mineable)

    asteroid = frozenset(mineable | wall)
    all_sv = frozenset(occupied)
    bbox = bbox_from_coords(all_sv if all_sv else frozenset(mineable))

    external_void: set[Coord] = set()
    if bbox.max_x >= bbox.min_x and bbox.max_y >= bbox.min_y:
        for x in range(bbox.min_x, bbox.max_x + 1):
            for y in range(bbox.min_y, bbox.max_y + 1):
                c = (x, y)
                if c not in occupied:
                    external_void.add(c)

    return NormalizedReconstructionTopology(
        mineable_cells=frozenset(mineable),
        wall_cells=frozenset(wall),
        interior_patch_cells=frozenset(interior_patch),
        external_void_cells=frozenset(external_void),
        asteroid_cells=asteroid,
        bbox=bbox,
    )


def normalize_topology_for_compare(
    topology: NormalizedReconstructionTopology,
) -> NormalizedReconstructionTopology:
    """Identity helper; sets already island-deduped."""

    return topology


def _cap_coords(coords: frozenset[Coord]) -> list[list[int | str]]:
    items: list[list[int | str]] = [list(c) for c in sorted(coords)]
    if len(items) <= _DIFF_LIST_CAP:
        return items
    extra = len(items) - _DIFF_LIST_CAP
    return items[:_DIFF_LIST_CAP] + [[f"...{extra} more"]]


def diff_topology(
    actual: NormalizedReconstructionTopology,
    expected: NormalizedReconstructionTopology,
) -> dict[str]:
    """Symmetric set diffs for fixture assertion messages."""

    missing_mineable = expected.mineable_cells - actual.mineable_cells
    extra_mineable = actual.mineable_cells - expected.mineable_cells
    missing_asteroid = expected.asteroid_cells - actual.asteroid_cells
    extra_asteroid = actual.asteroid_cells - expected.asteroid_cells
    wrong_external = actual.external_void_cells ^ expected.external_void_cells
    wrong_interior = actual.interior_patch_cells ^ expected.interior_patch_cells

    return {
        "missing_mineable_cells": _cap_coords(frozenset(missing_mineable)),
        "extra_mineable_cells": _cap_coords(frozenset(extra_mineable)),
        "missing_asteroid_cells": _cap_coords(frozenset(missing_asteroid)),
        "extra_asteroid_cells": _cap_coords(frozenset(extra_asteroid)),
        "wrong_external_void_cells": _cap_coords(frozenset(wrong_external)),
        "wrong_interior_patch_cells": _cap_coords(frozenset(wrong_interior)),
        "actual_bbox": {
            "min_x": actual.bbox.min_x,
            "max_x": actual.bbox.max_x,
            "min_y": actual.bbox.min_y,
            "max_y": actual.bbox.max_y,
        },
        "expected_bbox": {
            "min_x": expected.bbox.min_x,
            "max_x": expected.bbox.max_x,
            "min_y": expected.bbox.min_y,
            "max_y": expected.bbox.max_y,
        },
    }


def topology_diff_is_empty(diff: dict[str]) -> bool:
    for key in (
        "missing_mineable_cells",
        "extra_mineable_cells",
        "missing_asteroid_cells",
        "extra_asteroid_cells",
        "wrong_external_void_cells",
        "wrong_interior_patch_cells",
    ):
        items = diff.get(key, [])
        if not items:
            continue
        if len(items) == 1 and items[0] == ["...0 more"]:
            continue
        return False
    ab = diff.get("actual_bbox", {})
    eb = diff.get("expected_bbox", {})
    return bool(ab == eb)


def raw_coords_from_snapshot(snapshot: DecodedBlueprintSnapshotDTO) -> frozenset[RawCoord]:
    return frozenset((c.x, c.y) for c in snapshot.cells)


__all__ = [
    "NormalizedReconstructionTopology",
    "build_normalized_reconstruction_topology",
    "decode_shapez_copy_string",
    "diff_topology",
    "normalize_topology_for_compare",
    "raw_coords_from_snapshot",
    "topology_diff_is_empty",
]
