"""Optional candidate blueprint export from solver artifacts (PR-6)."""

from __future__ import annotations

import copy

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string, encode_copy_string
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


def _entry(x: int, y: int, *, tile: str, rotation: int = 0) -> dict[str]:
    return {"X": x, "Y": y, "R": rotation, "T": tile}


def assemble_candidate_blueprint(
    *,
    artifacts: GoldenSolverArtifacts,
    empty_copy: str,
) -> dict[str]:
    """Merge empty field shell with L3 equipment and L5 transport tiles."""

    root = copy.deepcopy(decode_copy_string(empty_copy.strip().removesuffix("$")).root)
    bp = root.setdefault("BP", {})
    if not isinstance(bp, dict):
        bp = {}
        root["BP"] = bp

    equipment_coords: set[Coord] = set()
    belt_coords: set[Coord] = set()
    new_entries: list[dict[str]] = []

    rim = artifacts.rim_result
    if rim is not None:
        for placement in rim.committed_placements:
            ax, ay = placement.anchor
            equipment_coords.add((ax, ay))
            new_entries.append(_entry(ax, ay, tile="Layout_ShapeMiner"))
            for ex, ey in placement.extension_cells:
                equipment_coords.add((ex, ey))
                new_entries.append(_entry(ex, ey, tile="Layout_ShapeMinerExtension"))

    inner = artifacts.inner_fill
    if inner is not None:
        for inner_placement in inner.placements:
            x, y = inner_placement.coord
            equipment_coords.add((x, y))

    route_plan = artifacts.route_plan
    if route_plan is not None:
        for tile in route_plan.transport_tiles:
            x, y = tile.coord
            belt_coords.add((x, y))
            new_entries.append(
                _entry(x, y, tile=tile.tile_id, rotation=tile.rotation),
            )
        for route in route_plan.routes:
            for x, y in route.path_coords:
                if (x, y) in belt_coords:
                    continue
                belt_coords.add((x, y))
                new_entries.append(_entry(x, y, tile="SpaceBelt_Forward"))

    kept: list[dict[str]] = []
    raw_entries = bp.get("Entries")
    if isinstance(raw_entries, list):
        for row in raw_entries:
            if not isinstance(row, dict):
                continue
            x = int(row.get("X") or 0)
            y = int(row.get("Y") or 0)
            if (x, y) in equipment_coords or (x, y) in belt_coords:
                continue
            kept.append(dict(row))

    merged = kept + new_entries
    merged.sort(key=lambda r: (int(r.get("X") or 0), int(r.get("Y") or 0), str(r.get("T") or "")))
    bp["Entries"] = merged
    bp.setdefault("$type", "Island")
    root["V"] = root.get("V", 1)
    return root


def encode_candidate_copy_string(
    *,
    artifacts: GoldenSolverArtifacts,
    empty_copy: str,
) -> str:
    root = assemble_candidate_blueprint(artifacts=artifacts, empty_copy=empty_copy)
    return encode_copy_string(root)


__all__ = [
    "assemble_candidate_blueprint",
    "encode_candidate_copy_string",
]
