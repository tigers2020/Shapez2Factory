"""Phase K2 — confirmed placement equipment materialization (extractor + extensions)."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.coord_transform import steps_from_canonical_e
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import MaterializationFailureReason, TransportKind
from django_apps.asteroid_lab.optimization.gene_projection import _translate
from django_apps.asteroid_lab.optimization.gene_template import (
    GeneTemplate,
    extension_attachments_parent_first,
)
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedEquipmentCell,
    MaterializedLayoutCells,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible


def _miner_tile_type(transport_kind: TransportKind) -> str:
    if transport_kind == TransportKind.SHAPE_BELT:
        return "Layout_ShapeMiner"
    if transport_kind == TransportKind.FLUID_PIPE:
        return "Layout_FluidMiner"
    msg = f"unsupported transport kind for equipment: {transport_kind!r}"
    raise ValueError(msg)


def _extension_tile_type(transport_kind: TransportKind) -> str:
    return _miner_tile_type(transport_kind) + "Extension"


def _extractor_cell_kind(transport_kind: TransportKind) -> str:
    if transport_kind == TransportKind.SHAPE_BELT:
        return "shape_miner"
    return "fluid_miner"


def _extension_cell_kind(transport_kind: TransportKind) -> str:
    if transport_kind == TransportKind.SHAPE_BELT:
        return "shape_miner_extension"
    return "fluid_miner_extension"


def _direction_child_to_parent_server(child: Coord, parent: Coord) -> str | None:
    """Cardinal direction from child toward parent on the server grid."""

    cx, cy = child
    px, py = parent
    dx, dy = px - cx, py - cy
    if (dx, dy) == (1, 0):
        return "e"
    if (dx, dy) == (-1, 0):
        return "w"
    if (dx, dy) == (0, 1):
        return "s"
    if (dx, dy) == (0, -1):
        return "n"
    return None


def _extension_rotation(
    *,
    transport_kind: TransportKind,
    parent_coord: Coord,
    child_coord: Coord,
    parent_cell_kind: str,
    parent_rotation: int,
) -> int:
    child_ck = _extension_cell_kind(transport_kind)
    dir_child_to_parent = _direction_child_to_parent_server(child_coord, parent_coord)
    if dir_child_to_parent is None:
        msg = "extension and parent are not 4-neighbors on server grid"
        raise ValueError(msg)
    for q in range(4):
        if ports_compatible(child_ck, q, parent_cell_kind, parent_rotation, dir_child_to_parent):
            return q
    msg = "no extension R links extension to parent"
    raise ValueError(msg)


def _server_coord_for_attachment(
    anchor: Coord,
    offset: Coord,
    steps: int,
) -> Coord:
    return _translate(anchor, offset, steps)


def preview_equipment_for_candidate(
    candidate: GeneCandidate,
    *,
    gene: GeneTemplate | None,
) -> tuple[MaterializedEquipmentCell, ...]:
    """Preview equipment cells for one candidate (replay overlay; not a commit)."""

    if gene is None:
        return ()
    return _equipment_cells_for_candidate(candidate, gene)


def _equipment_cells_for_candidate(
    candidate: GeneCandidate,
    gene: GeneTemplate,
) -> tuple[MaterializedEquipmentCell, ...]:
    """Build equipment cells for a single candidate (shared by preview + batch materialize)."""

    cells: list[MaterializedEquipmentCell] = []
    tk = candidate.transport_kind
    steps = steps_from_canonical_e(candidate.output_dir)
    extractor = candidate.extractor
    ext_rot: dict[Coord, int] = {}
    cells.append(
        MaterializedEquipmentCell(
            coord=extractor,
            tile_type=_miner_tile_type(tk),
            cell_kind=_extractor_cell_kind(tk),
            rotation=steps,
        )
    )
    if candidate.extensions and not gene.extension_attachments:
        return tuple(cells)

    materialized_extensions: set[Coord] = set()
    for edge in extension_attachments_parent_first(gene.extension_attachments):
        parent_server = _server_coord_for_attachment(extractor, edge.parent_offset, steps)
        child_server = _server_coord_for_attachment(extractor, edge.child_offset, steps)
        if child_server not in candidate.extensions:
            continue
        if parent_server == extractor:
            parent_kind = _extractor_cell_kind(tk)
            parent_r = steps
        else:
            parent_kind = _extension_cell_kind(tk)
            parent_r = ext_rot[parent_server]
        child_r = _extension_rotation(
            transport_kind=tk,
            parent_coord=parent_server,
            child_coord=child_server,
            parent_cell_kind=parent_kind,
            parent_rotation=parent_r,
        )
        ext_rot[child_server] = child_r
        materialized_extensions.add(child_server)
        cells.append(
            MaterializedEquipmentCell(
                coord=child_server,
                tile_type=_extension_tile_type(tk),
                cell_kind=_extension_cell_kind(tk),
                rotation=child_r,
            )
        )
    return tuple(sorted(cells, key=lambda c: (c.coord[1], c.coord[0], c.cell_kind)))


def materialize_confirmed_placements(
    commit: IncrementalCommitResult,
    candidates_by_id: Mapping[str, GeneCandidate],
    *,
    gene_templates_by_id: Mapping[str, GeneTemplate],
) -> tuple[MaterializedEquipmentCell, ...] | MaterializationFailureReason:
    """Emit extractor + extension cells for each CONFIRMED placement."""

    cells: list[MaterializedEquipmentCell] = []
    seen_coords: set[Coord] = set()

    for placement in commit.confirmed:
        candidate = candidates_by_id.get(placement.candidate_id)
        if candidate is None:
            return MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP
        gene = gene_templates_by_id.get(candidate.gene_id)
        if gene is None:
            return MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP

        per_candidate = _equipment_cells_for_candidate(candidate, gene)
        for ext in candidate.extensions:
            if ext not in {c.coord for c in per_candidate}:
                return MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP

        for eq in per_candidate:
            if eq.coord in seen_coords:
                return MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP
            seen_coords.add(eq.coord)
            cells.append(eq)

    return tuple(sorted(cells, key=lambda c: (c.coord[1], c.coord[0], c.cell_kind)))


def merge_materialized_layout(
    route_result: RouteMaterializationResult,
    equipment: tuple[MaterializedEquipmentCell, ...] | MaterializationFailureReason,
) -> RouteMaterializationResult:
    """Combine route materialization with placement equipment.

    Keeps ``cells`` and ``equipment_cells`` as separate tuples (no coord dict merge).
    On coord overlap, transport wins (equipment on shared trunk coords is dropped).
    Remaining overlap after drop is a hard failure.
    """

    if isinstance(equipment, MaterializationFailureReason):
        return RouteMaterializationResult(layout=None, failure_reason=equipment)
    if route_result.failure_reason is not None or route_result.layout is None:
        return route_result

    transport_coords = {c.coord for c in route_result.layout.cells}
    overlap = transport_coords & {eq.coord for eq in equipment}
    if overlap:
        # Shared trunk: belt/pipe owns the coord; drop equipment on transport cells.
        equipment = tuple(eq for eq in equipment if eq.coord not in overlap)
        overlap = transport_coords & {eq.coord for eq in equipment}
    if overlap:
        return RouteMaterializationResult(
            layout=None,
            failure_reason=MaterializationFailureReason.EQUIPMENT_TRANSPORT_COORD_OVERLAP,
        )

    return RouteMaterializationResult(
        layout=MaterializedLayoutCells(
            cells=route_result.layout.cells,
            equipment_cells=equipment,
        ),
        failure_reason=None,
    )


__all__ = [
    "materialize_confirmed_placements",
    "merge_materialized_layout",
    "preview_equipment_for_candidate",
]
