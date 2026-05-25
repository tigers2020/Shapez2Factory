"""Lab replay overlay projection for RTTP bundle footprints (read-only, PR-1).

UI/replay projection-owned. Must not be imported by incremental_commit, route probe,
selection, or validation modules.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.catalog.asteroid_transport_projection import resolve_route_tile
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4

_FLUID_FIELD_KIND = "asteroid_fluid_field"
_SHAPE_FIELD_KIND = "asteroid_shape_field"

_OUTPUT_DIR_TO_ROTATION: dict[str, int] = {"E": 0, "S": 1, "W": 2, "N": 3}
_CARDINAL_TO_ROTATION: dict[CardinalDirection, int] = {
    CardinalDirection.E: 0,
    CardinalDirection.S: 1,
    CardinalDirection.W: 2,
    CardinalDirection.N: 3,
}

_ROW_PRIORITY: dict[str, int] = {
    "shape_miner": 30,
    "fluid_miner": 30,
    "shape_miner_extension": 30,
    "fluid_miner_extension": 30,
    "space_belt": 20,
    "space_pipe": 20,
}


@dataclass(frozen=True, slots=True)
class PlacementOverlayDiagnostics:
    visible_miner_cell_count: int
    visible_extension_cell_count: int
    placement_route_overlap_warning_count: int
    placement_route_overlap_warning_coords: tuple[Coord, ...]


def _equipment_kinds(transport_kind: TransportKind) -> tuple[str, str, str, str]:
    if transport_kind is TransportKind.FLUID_PIPE:
        return (
            "fluid_miner",
            "fluid_miner_extension",
            "Layout_FluidMiner",
            "Layout_FluidMinerExtension",
        )
    return (
        "shape_miner",
        "shape_miner_extension",
        "Layout_ShapeMiner",
        "Layout_ShapeMinerExtension",
    )


def _transport_channel(transport_kind: TransportKind) -> tuple[str, str, str]:
    if transport_kind is TransportKind.FLUID_PIPE:
        return ("space_pipe", "SpacePipe_Forward", "fluid_pipe")
    return ("space_belt", "SpaceBelt_Forward", "shape_belt")


_DELTA_TO_DIR: dict[Coord, int] = {
    (1, 0): 0,
    (0, 1): 1,
    (-1, 0): 2,
    (0, -1): 3,
}


def _dir_between(from_coord: Coord, to_coord: Coord) -> int | None:
    dx = int(to_coord[0]) - int(from_coord[0])
    dy = int(to_coord[1]) - int(from_coord[1])
    if abs(dx) + abs(dy) != 1:
        return None
    return _DELTA_TO_DIR.get((dx, dy))


def _route_degree(coord: Coord, route_cells: frozenset[Coord]) -> int:
    return sum(1 for nb in neighbors4(coord) if nb in route_cells)


def _walk_route_chain(route_cells: frozenset[Coord], start: Coord) -> tuple[Coord, ...]:
    chain = [start]
    prev: Coord | None = None
    current = start
    visited = {start}
    while True:
        next_candidates = [
            nb
            for nb in neighbors4(current)
            if nb in route_cells and nb != prev and nb not in visited
        ]
        if not next_candidates:
            break
        nxt = next_candidates[0]
        chain.append(nxt)
        visited.add(nxt)
        prev, current = current, nxt
    return tuple(chain)


def _route_chains(route_cells: frozenset[Coord]) -> tuple[tuple[Coord, ...], ...]:
    remaining = set(route_cells)
    chains: list[tuple[Coord, ...]] = []
    while remaining:
        endpoints = [c for c in remaining if _route_degree(c, route_cells) == 1]
        start = (
            min(endpoints, key=lambda c: (c[1], c[0]))
            if endpoints
            else min(remaining, key=lambda c: (c[1], c[0]))
        )
        chain = _walk_route_chain(route_cells, start)
        for coord in chain:
            remaining.discard(coord)
        chains.append(chain)
    return tuple(chains)


def _flow_dirs_by_coord(
    route_cells: frozenset[Coord],
) -> dict[Coord, tuple[int | None, int | None]]:
    flow: dict[Coord, tuple[int | None, int | None]] = {}
    for chain in _route_chains(route_cells):
        for index, coord in enumerate(chain):
            incoming = _dir_between(chain[index - 1], coord) if index > 0 else None
            outgoing = _dir_between(coord, chain[index + 1]) if index + 1 < len(chain) else None
            flow[coord] = (incoming, outgoing)
    for coord in route_cells:
        flow.setdefault(coord, (None, None))
    return flow


def field_kind_map_from_entries(
    entries: Sequence[tuple[int, int, str]],
) -> dict[Coord, str]:
    return {(int(x), int(y)): kind for x, y, kind in entries}


def resolve_placement_transport_kind(
    candidate: BundleCandidate,
    field_kind_by_coord: Mapping[Coord, str] | None,
) -> TransportKind:
    """Prefer mineable field kind at extractor anchor over global ``candidate.transport_kind``."""

    if not field_kind_by_coord:
        return candidate.transport_kind
    anchor = candidate.anchor_coord
    pattern = candidate.pattern
    extractor_coord = (
        anchor[0] + pattern.extractor_offset[0],
        anchor[1] + pattern.extractor_offset[1],
    )
    for coord in (extractor_coord, anchor):
        field_kind = field_kind_by_coord.get(coord)
        if field_kind == _FLUID_FIELD_KIND:
            return TransportKind.FLUID_PIPE
        if field_kind == _SHAPE_FIELD_KIND:
            return TransportKind.SHAPE_BELT
    return candidate.transport_kind


def _rotation_for_candidate(candidate: BundleCandidate) -> int:
    ref = candidate.catalog_placement_ref
    if ref is not None:
        return _CARDINAL_TO_ROTATION[ref.rotation]
    return _OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0)


def _base_row(
    coord: Coord,
    *,
    kind: str | None,
    cell_kind: str,
    tile_type: str,
    transport_kind: str,
    overlay_semantic_kind: str,
    rotation: int,
    candidate_id: str,
    commit_state: str | None = None,
) -> dict[str, Any]:
    wire_kind = kind if kind is not None else overlay_semantic_kind
    wire_transport = "" if transport_kind == "none" else transport_kind
    row: dict[str, Any] = {
        "x": int(coord[0]),
        "y": int(coord[1]),
        "kind": wire_kind,
        "cell_kind": cell_kind,
        "tile_type": tile_type,
        "sprite_identifier": tile_type,
        "transport_kind": transport_kind,
        "transport": wire_transport,
        "rotation": rotation,
        "overlay_semantic_kind": overlay_semantic_kind,
        "candidate_id": candidate_id,
    }
    if commit_state is not None:
        row["commit_state"] = commit_state
    return row


def _rows_for_candidate(
    candidate: BundleCandidate,
    *,
    placement_transport_kind: TransportKind,
    extractor_semantic: str,
    extension_semantic: str,
    fixed_output_transport_semantic: str,
    stub_semantic: str,
    commit_state: str | None,
) -> list[dict[str, Any]]:
    miner_ck, ext_ck, miner_tt, ext_tt = _equipment_kinds(placement_transport_kind)
    belt_ck, belt_tt, belt_tk = _transport_channel(placement_transport_kind)
    rotation = _rotation_for_candidate(candidate)
    anchor = candidate.anchor_coord
    pattern = candidate.pattern

    def at(offset: Coord) -> Coord:
        return (anchor[0] + offset[0], anchor[1] + offset[1])

    rows: list[dict[str, Any]] = []
    rows.append(
        _base_row(
            at(pattern.extractor_offset),
            kind=extractor_semantic,
            cell_kind=miner_ck,
            tile_type=miner_tt,
            transport_kind="none",
            overlay_semantic_kind=extractor_semantic,
            rotation=rotation,
            candidate_id=candidate.candidate_id,
            commit_state=commit_state,
        )
    )
    rows.append(
        _base_row(
            at(pattern.fixed_output_transport_offset),
            kind=fixed_output_transport_semantic,
            cell_kind=belt_ck,
            tile_type=belt_tt,
            transport_kind=belt_tk,
            overlay_semantic_kind=fixed_output_transport_semantic,
            rotation=_OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0),
            candidate_id=candidate.candidate_id,
            commit_state=commit_state,
        )
    )
    for offset in pattern.extension_offsets:
        rows.append(
            _base_row(
                at(offset),
                kind=extension_semantic,
                cell_kind=ext_ck,
                tile_type=ext_tt,
                transport_kind="none",
                overlay_semantic_kind=extension_semantic,
                rotation=rotation,
                candidate_id=candidate.candidate_id,
                commit_state=commit_state,
            )
        )
    rows.append(
        _base_row(
            candidate.output_stub,
            kind=stub_semantic,
            cell_kind=belt_ck,
            tile_type=belt_tt,
            transport_kind=belt_tk,
            overlay_semantic_kind=stub_semantic,
            rotation=_OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0),
            candidate_id=candidate.candidate_id,
            commit_state=commit_state,
        )
    )
    return rows


def _route_rows(
    coords: frozenset[Coord],
    *,
    transport_kind: TransportKind,
    candidate_id: str = "",
) -> list[dict[str, Any]]:
    belt_ck, _default_tt, belt_tk = _transport_channel(transport_kind)
    flow_dirs = _flow_dirs_by_coord(coords)
    rows: list[dict[str, Any]] = []
    for coord in sorted(coords, key=lambda c: (c[1], c[0])):
        incoming, outgoing = flow_dirs.get(coord, (None, None))
        projected = resolve_route_tile(
            transport_kind=transport_kind,
            incoming_dir=incoming,
            outgoing_dir=outgoing,
        )
        tile_type = projected.layout_t
        rotation = projected.display_rotation_q
        rows.append(
            _base_row(
                coord,
                kind="route.committed_path",
                cell_kind=belt_ck,
                tile_type=tile_type,
                transport_kind=belt_tk,
                overlay_semantic_kind="route.committed_path",
                rotation=rotation,
                candidate_id=candidate_id,
            )
        )
    return rows


def merge_overlay_rows_by_priority(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_coord: dict[Coord, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        coord = (int(row["x"]), int(row["y"]))
        ck = str(row.get("cell_kind") or row.get("kind") or "")
        priority = _ROW_PRIORITY.get(ck, int(row.get("priority", 0)))
        existing = by_coord.get(coord)
        if existing is None or priority > _ROW_PRIORITY.get(
            str(existing.get("cell_kind") or existing.get("kind") or ""),
            0,
        ):
            by_coord[coord] = row
    return list(by_coord.values())


def build_candidate_placement_overlay_rows(
    candidates: Sequence[BundleCandidate],
    *,
    field_kind_by_coord: Mapping[Coord, str] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        placement_transport = resolve_placement_transport_kind(
            candidate,
            field_kind_by_coord,
        )
        out.extend(
            _rows_for_candidate(
                candidate,
                placement_transport_kind=placement_transport,
                extractor_semantic="placement.candidate_extractor",
                extension_semantic="placement.candidate_extension",
                fixed_output_transport_semantic="placement.candidate_fixed_output_transport",
                stub_semantic="placement.candidate_output_stub",
                commit_state=None,
            )
        )
    return out


def build_selected_placement_overlay_rows(
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    *,
    field_kind_by_coord: Mapping[Coord, str] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cid in commit_order:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        placement_transport = resolve_placement_transport_kind(
            candidate,
            field_kind_by_coord,
        )
        out.extend(
            _rows_for_candidate(
                candidate,
                placement_transport_kind=placement_transport,
                extractor_semantic="placement.selected_extractor",
                extension_semantic="placement.selected_extension",
                fixed_output_transport_semantic="placement.selected_fixed_output_transport",
                stub_semantic="placement.selected_output_stub",
                commit_state=None,
            )
        )
    return out


def build_confirmed_placement_overlay_rows(
    *,
    committed_ids: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    reserved_route_cells: frozenset[Coord],
    field_kind_by_coord: Mapping[Coord, str] | None = None,
) -> tuple[list[dict[str, Any]], PlacementOverlayDiagnostics]:
    placement_rows: list[dict[str, Any]] = []
    route_coords: set[Coord] = set(reserved_route_cells)
    overlap_coords: list[Coord] = []
    miner_count = 0
    ext_count = 0
    transport = TransportKind.SHAPE_BELT

    for cid in committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        transport = resolve_placement_transport_kind(candidate, field_kind_by_coord)
        bundle_rows = _rows_for_candidate(
            candidate,
            placement_transport_kind=transport,
            extractor_semantic="placement.confirmed_extractor",
            extension_semantic="placement.confirmed_extension",
            fixed_output_transport_semantic="placement.confirmed_fixed_output_transport",
            stub_semantic="placement.confirmed_output_stub",
            commit_state="confirmed",
        )
        for coord in candidate.occupied_cells:
            if coord in reserved_route_cells:
                overlap_coords.append(coord)
        miner_count += 1
        ext_count += len(candidate.pattern.extension_offsets)
        placement_rows.extend(bundle_rows)
        route_coords -= candidate.occupied_cells
        fot_coord = (
            candidate.anchor_coord[0] + candidate.pattern.fixed_output_transport_offset[0],
            candidate.anchor_coord[1] + candidate.pattern.fixed_output_transport_offset[1],
        )
        route_coords.discard(fot_coord)
        route_coords.discard(candidate.output_stub)

    route_rows = _route_rows(frozenset(route_coords), transport_kind=transport)
    merged = merge_overlay_rows_by_priority(placement_rows + route_rows)

    unique_overlaps = tuple(sorted(set(overlap_coords)))
    diag = PlacementOverlayDiagnostics(
        visible_miner_cell_count=miner_count,
        visible_extension_cell_count=ext_count,
        placement_route_overlap_warning_count=len(unique_overlaps),
        placement_route_overlap_warning_coords=unique_overlaps,
    )
    return merged, diag


__all__ = [
    "PlacementOverlayDiagnostics",
    "build_candidate_placement_overlay_rows",
    "build_confirmed_placement_overlay_rows",
    "build_selected_placement_overlay_rows",
    "field_kind_map_from_entries",
    "merge_overlay_rows_by_priority",
    "resolve_placement_transport_kind",
]
