"""Normalized reconstruction topology for fixture pair acceptance (Server X/Y only)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    infer_topology_coord_frame,
    topology_coord_for_cell,
)
from django_apps.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    MINER_EXTENSION_CELL_KINDS,
    is_asteroid_evidence,
)
from django_apps.asteroid_lab.reconstruction.grid import Coord as RawCoord
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.grid_contract import BBox, Coord, bbox_from_coords
from django_apps.asteroid_lab.snapshots.server_coords import (
    map_bbox_dense_and_y,
    server_xy_for_raw_xy,
)

_DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "asteroid_lab"
_DIFF_LIST_CAP = 50


@dataclass(frozen=True, slots=True)
class NormalizedReconstructionTopology:
    """Server-grid topology sets for compare (layer duplicates collapse to ``(sx, sy)``)."""

    mineable_cells: frozenset[Coord]
    wall_cells: frozenset[Coord]
    interior_patch_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    asteroid_cells: frozenset[Coord]
    bbox: BBox
    server_xy_params: tuple[int, int] | None


def _fixtures_dir(fixtures_dir: Path | None) -> Path:
    return fixtures_dir if fixtures_dir is not None else _DEFAULT_FIXTURES_DIR


def load_shapez_copy_string_fixture_lines(path: Path | str) -> tuple[str, ...]:
    """All non-empty lines; trailing ``$`` stripped."""

    text = Path(path).read_text(encoding="utf-8")
    return tuple(ln.strip().removesuffix("$") for ln in text.splitlines() if ln.strip())


def load_shapez_copy_string_fixture(path: Path | str) -> str:
    """First non-empty line (single-map helper)."""

    lines = load_shapez_copy_string_fixture_lines(path)
    if not lines:
        msg = f"fixture has no copy string lines: {path}"
        raise ValueError(msg)
    return lines[0]


def load_reconstruction_fixture_line_pairs(
    required_name: str = "reconstruction_required_.txt",
    solved_name: str = "reconstruction_complete_solved.txt",
    *,
    fixtures_dir: Path | None = None,
) -> tuple[tuple[str, str], ...]:
    """``(required_copy, solved_copy)`` per line index."""

    base = _fixtures_dir(fixtures_dir)
    req_lines = load_shapez_copy_string_fixture_lines(base / required_name)
    sol_lines = load_shapez_copy_string_fixture_lines(base / solved_name)
    if len(req_lines) != len(sol_lines):
        msg = (
            f"fixture line count mismatch: {required_name} has {len(req_lines)} lines, "
            f"{solved_name} has {len(sol_lines)} lines"
        )
        raise ValueError(msg)
    return tuple(zip(req_lines, sol_lines, strict=True))


def decode_shapez_copy_string(copy_string: str) -> DecodedBlueprintSnapshotDTO:
    """Decode + normalize + snapshot DTO."""

    norm = normalize_decoded_blueprint(decode_copy_string(copy_string.strip().removesuffix("$")))
    return build_decoded_blueprint_snapshot(norm.decoded_json)


def _params_from_cells(cells: Sequence[DecodedCellDTO]) -> tuple[int, int] | None:
    rows = [{"X": c.x, "Y": c.y} for c in cells]
    return map_bbox_dense_and_y(rows)


def _is_mineable_occupied(cell: DecodedCellDTO) -> bool:
    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        return True
    return cell.cell_kind in MINER_EXTENSION_CELL_KINDS


def _shell_topology_coords(
    shell_raw_coords: frozenset[RawCoord] | None,
    params: tuple[int, int] | None,
    *,
    coord_frame: CoordFrame,
) -> frozenset[Coord]:
    if not shell_raw_coords:
        return frozenset()
    if coord_frame == CoordFrame.ISLAND_RAW:
        return frozenset(shell_raw_coords)
    if params is None:
        return frozenset()
    md, my = int(params[0]), int(params[1])
    hz = bool(params[2]) if len(params) > 2 else False
    return frozenset(
        server_xy_for_raw_xy(x, y, min_dense_x=md, min_raw_y=my, has_explicit_raw_x_zero=hz)
        for x, y in shell_raw_coords
    )


def build_normalized_reconstruction_topology(
    cells: Sequence[DecodedCellDTO],
    *,
    server_xy_params: tuple[int, int] | None = None,
    shell_raw_coords: frozenset[RawCoord] | None = None,
    coord_frame: CoordFrame | None = None,
) -> NormalizedReconstructionTopology:
    """Build compare topology from decoded or reconstruction-merged cells."""

    params = server_xy_params if server_xy_params is not None else _params_from_cells(cells)
    frame = coord_frame if coord_frame is not None else infer_topology_coord_frame(cells)
    mineable: set[Coord] = set()
    wall: set[Coord] = set()
    occupied: set[Coord] = set()

    for cell in cells:
        try:
            sv = topology_coord_for_cell(cell, params, coord_frame=frame)
        except ValueError:
            continue
        occupied.add(sv)
        if _is_mineable_occupied(cell):
            mineable.add(sv)
        elif is_asteroid_evidence(cell):
            wall.add(sv)

    shell_sv = _shell_topology_coords(shell_raw_coords, params, coord_frame=frame)
    interior_patch = mineable - shell_sv if shell_sv else frozenset(mineable)

    asteroid = frozenset(mineable | wall)
    all_sv = frozenset(occupied)
    bbox = bbox_from_coords(all_sv if all_sv else frozenset(mineable))

    external_void: set[Coord] = set()
    if bbox.max_sx >= bbox.min_sx and bbox.max_sy >= bbox.min_sy:
        for sx in range(bbox.min_sx, bbox.max_sx + 1):
            for sy in range(bbox.min_sy, bbox.max_sy + 1):
                c = (sx, sy)
                if c not in occupied:
                    external_void.add(c)

    return NormalizedReconstructionTopology(
        mineable_cells=frozenset(mineable),
        wall_cells=frozenset(wall),
        interior_patch_cells=frozenset(interior_patch),
        external_void_cells=frozenset(external_void),
        asteroid_cells=asteroid,
        bbox=bbox,
        server_xy_params=params,
    )


def normalize_topology_for_compare(
    topology: NormalizedReconstructionTopology,
) -> NormalizedReconstructionTopology:
    """Identity helper; sets already server-deduped."""

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
) -> dict[str, Any]:
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
            "min_sx": actual.bbox.min_sx,
            "max_sx": actual.bbox.max_sx,
            "min_sy": actual.bbox.min_sy,
            "max_sy": actual.bbox.max_sy,
        },
        "expected_bbox": {
            "min_sx": expected.bbox.min_sx,
            "max_sx": expected.bbox.max_sx,
            "min_sy": expected.bbox.min_sy,
            "max_sy": expected.bbox.max_sy,
        },
    }


def topology_diff_is_empty(diff: dict[str, Any]) -> bool:
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
    "load_reconstruction_fixture_line_pairs",
    "load_shapez_copy_string_fixture",
    "load_shapez_copy_string_fixture_lines",
    "normalize_topology_for_compare",
    "raw_coords_from_snapshot",
    "topology_diff_is_empty",
]
