"""Project miner_seed_v2 decoded_json onto a rim anchor (map-absolute coords)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from django_apps.asteroid_lab.genetic_sample.coord_transform import (
    rotate_offset,
    steps_from_canonical_e,
)
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import LAYOUT_TYPE_SHAPE_TO_FLUID
from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    BundleCellRole,
    BundlePlacement,
    CandidateRejectReason,
    Layer03Slug,
)
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_MINING_BUNDLES
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import MinerSeedEntry
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.transport_entry import (
    derive_transport_entry_coord,
)
from django_apps.asteroid_lab.layers.shared.equivalence_key import (
    build_equivalence_key_from_candidate,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_MINING_CELL_KINDS = frozenset(
    {
        "shape_miner",
        "fluid_miner",
        "shape_miner_extension",
        "fluid_miner_extension",
    }
)
_TRANSPORT_CELL_KINDS = frozenset({"space_belt", "space_pipe"})


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    candidate: BundleCandidate | None
    reject_reason: CandidateRejectReason | None


def _layout_for_resource(layout_t: str, resource_kind: ResourceKind) -> str:
    if resource_kind == ResourceKind.SHAPE:
        return layout_t
    return LAYOUT_TYPE_SHAPE_TO_FLUID.get(layout_t, layout_t)


def _cell_role_from_layout(layout_t: str) -> BundleCellRole | None:
    cell_kind, _ = classify_blueprint_entry(layout_t)
    if cell_kind in ("shape_miner", "fluid_miner"):
        return BundleCellRole.MINER
    if cell_kind in ("shape_miner_extension", "fluid_miner_extension"):
        return BundleCellRole.EXTENSION
    if cell_kind in _TRANSPORT_CELL_KINDS:
        return BundleCellRole.TRANSPORT_STUB
    return None


def project_miner_seed_at_anchor(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    resource_kind: ResourceKind,
    transport_kind: TransportKind,
    complete_map: ReconstructionCompleteMap,
) -> ProjectionResult:
    snap = build_decoded_blueprint_snapshot(seed.decoded_json)
    extractor_local: Coord | None = None
    for cell in snap.cells:
        if cell.cell_kind in ("shape_miner", "fluid_miner"):
            extractor_local = (cell.x, cell.y)
            break
    if extractor_local is None:
        return ProjectionResult(
            candidate=None,
            reject_reason=CandidateRejectReason.LOCAL_GEOMETRY_INVALID,
        )

    steps = steps_from_canonical_e(output_dir)
    placements: list[BundlePlacement] = []
    mining_cells: set[Coord] = set()
    transport_cells: set[Coord] = set()

    for cell in snap.cells:
        role_kind = cell.cell_kind
        if role_kind not in _MINING_CELL_KINDS and role_kind not in _TRANSPORT_CELL_KINDS:
            continue
        offset = (cell.x - extractor_local[0], cell.y - extractor_local[1])
        map_coord = (
            anchor_coord[0] + rotate_offset(offset, steps)[0],
            anchor_coord[1] + rotate_offset(offset, steps)[1],
        )
        layout_t = _layout_for_resource(cell.tile_type, resource_kind)
        cell_role = _cell_role_from_layout(layout_t)
        if cell_role is None:
            return ProjectionResult(
                candidate=None,
                reject_reason=CandidateRejectReason.LOCAL_GEOMETRY_INVALID,
            )
        rotation = (cell.rotation + steps) % 4
        placements.append(
            BundlePlacement(
                coord=map_coord,
                layout_t=layout_t,
                rotation=rotation,
                cell_role=cell_role,
            )
        )
        if cell_role is BundleCellRole.TRANSPORT_STUB:
            transport_cells.add(map_coord)
        else:
            mining_cells.add(map_coord)

    if anchor_coord not in mining_cells:
        return ProjectionResult(
            candidate=None,
            reject_reason=CandidateRejectReason.LOCAL_GEOMETRY_INVALID,
        )

    if mining_cells - complete_map.field_cells:
        return ProjectionResult(
            candidate=None,
            reject_reason=CandidateRejectReason.MINING_CELL_OFF_FIELD,
        )

    transport_entry = derive_transport_entry_coord(
        anchor_coord=anchor_coord,
        output_dir=output_dir,
    )
    if transport_entry in mining_cells:
        return ProjectionResult(
            candidate=None,
            reject_reason=CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT,
        )

    if mining_cells & transport_cells:
        return ProjectionResult(
            candidate=None,
            reject_reason=CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT,
        )

    candidate_id = (
        f"layer_03:{seed.gene_key}:{anchor_coord[0]}:{anchor_coord[1]}:"
        f"{output_dir.value}:{steps}:{transport_kind.value}"
    )
    candidate = BundleCandidate(
        candidate_id=candidate_id,
        layer_slug=cast(Layer03Slug, LAYER_03_RIM_MINING_BUNDLES),
        gene_key=seed.gene_key,
        pattern_id=seed.pattern_id,
        intrinsic_priority_rank=seed.intrinsic_priority_rank,
        anchor_coord=anchor_coord,
        output_dir=output_dir,
        rotation=steps,
        resource_kind=resource_kind,
        transport_kind=transport_kind,
        equivalence_key="",
        mining_occupied_cells=frozenset(mining_cells),
        transport_stub_cells=frozenset(transport_cells),
        route_probe_start_coord=transport_entry,
        placements=tuple(placements),
        throughput_factor=seed.throughput_factor,
        topology_signature=seed.topology_signature,
    )
    equiv = build_equivalence_key_from_candidate(candidate)
    candidate = BundleCandidate(
        candidate_id=candidate.candidate_id,
        layer_slug=candidate.layer_slug,
        gene_key=candidate.gene_key,
        pattern_id=candidate.pattern_id,
        intrinsic_priority_rank=candidate.intrinsic_priority_rank,
        anchor_coord=candidate.anchor_coord,
        output_dir=candidate.output_dir,
        rotation=candidate.rotation,
        resource_kind=candidate.resource_kind,
        transport_kind=candidate.transport_kind,
        equivalence_key=equiv,
        mining_occupied_cells=candidate.mining_occupied_cells,
        transport_stub_cells=candidate.transport_stub_cells,
        route_probe_start_coord=candidate.route_probe_start_coord,
        placements=candidate.placements,
        throughput_factor=candidate.throughput_factor,
        topology_signature=candidate.topology_signature,
    )
    return ProjectionResult(candidate=candidate, reject_reason=None)


def local_geometry_invalid_detail(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    resource_kind: ResourceKind,
    complete_map: ReconstructionCompleteMap,
) -> str:
    """Dotted subreason for histogram when projection would fail LOCAL_GEOMETRY_INVALID."""
    del complete_map
    snap = build_decoded_blueprint_snapshot(seed.decoded_json)
    extractor_local: Coord | None = None
    for cell in snap.cells:
        if cell.cell_kind in ("shape_miner", "fluid_miner"):
            extractor_local = (cell.x, cell.y)
            break
    if extractor_local is None:
        return "local_geometry_invalid.missing_extractor"

    steps = steps_from_canonical_e(output_dir)
    mining_cells: set[Coord] = set()
    for cell in snap.cells:
        role_kind = cell.cell_kind
        if role_kind not in _MINING_CELL_KINDS:
            continue
        layout_t = _layout_for_resource(cell.tile_type, resource_kind)
        cell_role = _cell_role_from_layout(layout_t)
        if cell_role is None:
            return "local_geometry_invalid.unknown_layout"
        offset = (cell.x - extractor_local[0], cell.y - extractor_local[1])
        map_coord = (
            anchor_coord[0] + rotate_offset(offset, steps)[0],
            anchor_coord[1] + rotate_offset(offset, steps)[1],
        )
        if cell_role is not BundleCellRole.TRANSPORT_STUB:
            mining_cells.add(map_coord)

    if anchor_coord not in mining_cells:
        return "local_geometry_invalid.anchor_not_in_mining_cells"
    return "local_geometry_invalid.unclassified"


__all__ = [
    "ProjectionResult",
    "local_geometry_invalid_detail",
    "project_miner_seed_at_anchor",
]
