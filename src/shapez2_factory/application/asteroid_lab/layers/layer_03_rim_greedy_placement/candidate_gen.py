"""Layer 03 candidate generation (spec R2/R3/R4/R5/D1/D2) — Phase 1, no commit.

For each ``(rim anchor, gene entry, output direction in anchor.void_dirs)`` this module:

1. Orients the gene's canonical-East footprint to the chosen output direction (R4) and
   projects it onto the canonical solver coordinate frame with the extractor at the
   anchor cell.
2. Validates local geometry: every equipment cell must lie on the matching-resource
   field (R2) and the void-side output stub must lie in external void (R3).
3. Runs an immediate weighted route probe from ``route_probe_start`` to the nearest
   matching L2 trunk connector goal (belt for shape, pipe for fluid) (R5). Void cells are
   cheap to route through, field cells are costed higher; the candidate's own equipment
   is a hard blocker.

Route-feasible candidates form the *normal pool*; everything else lands in the diagnostic
reject pool. This module never commits (R6) and never consumes replay/metrics as input.

Determinism (D1): the normal pool is emitted sorted by
``(anchor_row, anchor_col, output_dir_rank, -throughput_factor, gene_id)`` in the canonical
solver frame. This enumeration order is NOT a commit selector (D2 — a later phase scores).
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, cast

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    BundleCellRole,
    BundlePlacement,
    CandidateRejectReason,
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    Layer03Slug,
    RimBundleCandidateSet,
    RouteProbedBundleCandidate,
    RouteProbeStatus,
    build_rim_bundle_candidate_set,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer03_observability import (
    build_layer03_observability,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_MINING_BUNDLES,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
    map_resource_kind_to_transport_kind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchor_scan import (  # noqa: E501
    RimAnchor,
    scan_rim_anchors,
)
from shapez2_factory.application.asteroid_lab.layers.shared.route_probe import weighted_route_probe
from shapez2_factory.domain.asteroid_lab.genetic_sample.enums import Direction
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, bbox_from_coords
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    mineable_field_kind_by_coord,
)

if TYPE_CHECKING:
    from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import (
        GeneCatalogEntry,
        GeneCatalogSnapshot,
    )
    from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
        ExteriorConnectionPlan,
    )

# Canonical cardinal edge values (shared with rim_anchor_scan / L2 slots).
_CARDINAL_DELTA: dict[str, Coord] = {
    "north": (0, -1),
    "east": (1, 0),
    "south": (0, 1),
    "west": (-1, 0),
}
_CARDINAL_TO_DIRECTION: dict[str, Direction] = {
    "north": Direction.N,
    "east": Direction.E,
    "south": Direction.S,
    "west": Direction.W,
}
# Fixed NESW rank shared with the rim anchor scan / D1 ordering.
_DIRECTION_RANK: dict[Direction, int] = {
    Direction.N: 0,
    Direction.E: 1,
    Direction.S: 2,
    Direction.W: 3,
}
_FIELD_KIND_TO_RESOURCE: dict[str, ResourceKind] = {
    "shape": ResourceKind.SHAPE,
    "fluid": ResourceKind.FLUID,
}
_PER_CELL_KIND_TO_FIELD: dict[str, str] = {
    "asteroid_shape_field": "shape",
    "asteroid_fluid_field": "fluid",
}
_THROUGHPUT_PRIORITY_RANK: dict[int, int] = {16: 0, 12: 1, 8: 2, 4: 3}


def output_dir_rank(direction: Direction) -> int:
    """Fixed NESW rank used by the D1 candidate ordering."""

    return _DIRECTION_RANK[direction]


def rotate_offset_east_to(offset: Coord, edge: str) -> Coord:
    """Rotate a canonical East-pointing ``(x, y)`` offset so output faces ``edge``.

    Solver frame is y-down (+x East, +y South). The rotation maps the canonical output
    vector ``(1, 0)`` onto the target cardinal unit vector while remaining a proper
    rotation, so the inward extensions follow consistently:

    * east  → identity        ``(x, y)``
    * north → ``(y, -x)``
    * west  → ``(-x, -y)``
    * south → ``(-y, x)``
    """

    x, y = offset
    if edge == "east":
        return (x, y)
    if edge == "north":
        return (y, -x)
    if edge == "west":
        return (-x, -y)
    if edge == "south":
        return (-y, x)
    msg = f"unknown cardinal edge: {edge!r}"
    raise ValueError(msg)


def _resource_eligible(entry_resource_kind: str, field_kind: str) -> bool:
    if entry_resource_kind == "both":
        return field_kind in _FIELD_KIND_TO_RESOURCE
    return entry_resource_kind == field_kind


def _equipment_matches_field(
    equipment_cells: frozenset[Coord],
    *,
    field_cells: frozenset[Coord],
    field_kind: str,
    kind_by_coord: dict[Coord, str],
) -> bool:
    """Equipment ⊆ field of the matching resource kind (R2).

    When per-cell evidence is available (decoded ``cells``) every equipment cell whose
    kind is known must equal the anchor's field kind; otherwise field membership alone
    governs (synthetic fixtures carry no decoded cells).
    """

    if not equipment_cells <= field_cells:
        return False
    for cell in equipment_cells:
        cell_kind = kind_by_coord.get(cell)
        if cell_kind is None:
            continue
        if _PER_CELL_KIND_TO_FIELD.get(cell_kind) != field_kind:
            return False
    return True


def _build_candidate(
    *,
    anchor: RimAnchor,
    entry: GeneCatalogEntry,
    edge: str,
    resource_kind: ResourceKind,
    equipment_cells: frozenset[Coord],
    extractor_cell: Coord,
    extension_cells: frozenset[Coord],
    stub_cell: Coord,
    route_probe_start: Coord,
) -> BundleCandidate:
    direction = _CARDINAL_TO_DIRECTION[edge]
    rotation = output_dir_rank(direction)
    transport_kind = map_resource_kind_to_transport_kind(resource_kind)
    ax, ay = anchor.coord
    candidate_id = (
        f"layer_03:{entry.gene_id}:{ax}:{ay}:"
        f"{direction.value}:{rotation}:{transport_kind.value}"
    )
    equivalence_key = (
        f"{transport_kind.value}|{tuple(sorted(equipment_cells))}|{stub_cell}|{route_probe_start}"
    )
    miner_layout = (
        "Layout_ShapeMiner" if resource_kind is ResourceKind.SHAPE else "Layout_FluidMiner"
    )
    stub_layout = (
        "SpaceBelt_Forward" if transport_kind is TransportKind.SHAPE_BELT else "SpacePipe_Forward"
    )
    placements: list[BundlePlacement] = [
        BundlePlacement(
            coord=extractor_cell,
            layout_t=miner_layout,
            rotation=rotation,
            cell_role=BundleCellRole.MINER,
        )
    ]
    for cell in sorted(extension_cells):
        placements.append(
            BundlePlacement(
                coord=cell,
                layout_t="Layout_MinerExtension",
                rotation=rotation,
                cell_role=BundleCellRole.EXTENSION,
            )
        )
    placements.append(
        BundlePlacement(
            coord=stub_cell,
            layout_t=stub_layout,
            rotation=rotation,
            cell_role=BundleCellRole.TRANSPORT_STUB,
        )
    )
    return BundleCandidate(
        candidate_id=candidate_id,
        layer_slug=cast(Layer03Slug, LAYER_03_RIM_MINING_BUNDLES),
        gene_key=entry.gene_id,
        pattern_id=entry.topology_signature_base or entry.gene_id,
        intrinsic_priority_rank=_THROUGHPUT_PRIORITY_RANK.get(entry.throughput_factor, 9),
        anchor_coord=anchor.coord,
        output_dir=direction,
        rotation=rotation,
        resource_kind=resource_kind,
        transport_kind=transport_kind,
        equivalence_key=equivalence_key,
        mining_occupied_cells=equipment_cells,
        transport_stub_cells=frozenset({stub_cell}),
        route_probe_start_coord=route_probe_start,
        placements=tuple(placements),
        throughput_factor=entry.throughput_factor,
        topology_signature=f"{entry.topology_signature_base or entry.gene_id}:{direction.value}",
    )


def _diagnostic_reject(
    candidate: BundleCandidate,
    *,
    reason: CandidateRejectReason,
    status: RouteProbeStatus,
) -> RouteProbedBundleCandidate:
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=status,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=reason,
    )


def _d1_key(probed: RouteProbedBundleCandidate) -> tuple[int, int, int, int, str]:
    cand = probed.candidate
    return (
        cand.anchor_coord[0],
        cand.anchor_coord[1],
        output_dir_rank(cand.output_dir),
        -cand.throughput_factor,
        cand.gene_key,
    )


def generate_candidates(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    gene_catalog: GeneCatalogSnapshot,
    anchors: tuple[RimAnchor, ...] | None = None,
) -> RimBundleCandidateSet:
    """Deterministic rim candidate pool with immediate route probe (no commit).

    Returns a :class:`RimBundleCandidateSet` whose ``normal_candidates`` are route-feasible
    and emitted in D1 order, and whose ``diagnostic_rejected_candidates`` capture geometry /
    route failures for observability.
    """

    if anchors is None:
        anchors = scan_rim_anchors(complete_map)

    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    kind_by_coord = mineable_field_kind_by_coord(complete_map)

    route_goals: tuple[RouteGoal, ...] = ()
    if exterior_plan is not None:
        route_goals = build_layer03_route_goals(
            exterior_plan, transport_kind=TransportKind.SHAPE_BELT
        ) + build_layer03_route_goals(exterior_plan, transport_kind=TransportKind.FLUID_PIPE)

    base_walkable = field_cells | external_void
    search_bbox = bbox_from_coords(base_walkable)

    normal: list[RouteProbedBundleCandidate] = []
    diagnostics: list[RouteProbedBundleCandidate] = []

    seed_projection_attempts = 0
    geometry_rejected = 0
    route_probe_attempts = 0

    for anchor in anchors:
        for edge in anchor.void_dirs:
            for entry in gene_catalog.entries:
                if not _resource_eligible(entry.resource_kind, anchor.field_kind):
                    continue
                seed_projection_attempts += 1

                resource_kind = _FIELD_KIND_TO_RESOURCE[anchor.field_kind]
                extractor_cell = (
                    anchor.coord[0] + rotate_offset_east_to(entry.extractor_offset, edge)[0],
                    anchor.coord[1] + rotate_offset_east_to(entry.extractor_offset, edge)[1],
                )
                equipment_offsets = (
                    {entry.extractor_offset}
                    | set(entry.extension_offsets)
                    | set(entry.occupied_offsets)
                )
                equipment_cells = frozenset(
                    (
                        anchor.coord[0] + rotate_offset_east_to(off, edge)[0],
                        anchor.coord[1] + rotate_offset_east_to(off, edge)[1],
                    )
                    for off in equipment_offsets
                )
                extension_cells = equipment_cells - {extractor_cell}
                stub_delta = rotate_offset_east_to(entry.output_stub_offset, edge)
                stub_cell = (anchor.coord[0] + stub_delta[0], anchor.coord[1] + stub_delta[1])
                start_delta = rotate_offset_east_to(entry.route_probe_start_offset, edge)
                route_probe_start = (
                    anchor.coord[0] + start_delta[0],
                    anchor.coord[1] + start_delta[1],
                )

                candidate = _build_candidate(
                    anchor=anchor,
                    entry=entry,
                    edge=edge,
                    resource_kind=resource_kind,
                    equipment_cells=equipment_cells,
                    extractor_cell=extractor_cell,
                    extension_cells=extension_cells,
                    stub_cell=stub_cell,
                    route_probe_start=route_probe_start,
                )

                # R2: equipment ⊆ matching-resource field.
                if not _equipment_matches_field(
                    equipment_cells,
                    field_cells=field_cells,
                    field_kind=anchor.field_kind,
                    kind_by_coord=kind_by_coord,
                ):
                    geometry_rejected += 1
                    diagnostics.append(
                        _diagnostic_reject(
                            candidate,
                            reason=CandidateRejectReason.MINING_CELL_OFF_FIELD,
                            status=RouteProbeStatus.SKIPPED_GEOMETRY,
                        )
                    )
                    continue

                # R3: output stub ⊆ external void.
                if stub_cell not in external_void:
                    geometry_rejected += 1
                    diagnostics.append(
                        _diagnostic_reject(
                            candidate,
                            reason=CandidateRejectReason.TRANSPORT_STUB_NOT_IN_VOID,
                            status=RouteProbeStatus.SKIPPED_GEOMETRY,
                        )
                    )
                    continue

                # R5: immediate weighted route probe (void cheap, field costed, own
                # equipment is a hard blocker).
                walkable = base_walkable - equipment_cells
                field_cost = field_cells - equipment_cells
                domain = WeightedTransportRouteDomain(
                    search_bbox=search_bbox,
                    blocked_cells=equipment_cells,
                    walkable_cells=walkable,
                    field_cost_cells=field_cost,
                )
                route_probe_attempts += 1
                probed = weighted_route_probe(
                    candidate=candidate,
                    route_goals=route_goals,
                    domain=domain,
                    field_cells=field_cells,
                )
                if probed.route_probe_status == RouteProbeStatus.SUCCEEDED:
                    normal.append(probed)
                else:
                    diagnostics.append(probed)

    normal.sort(key=_d1_key)
    diagnostics.sort(key=_d1_key)

    reject_counts = Counter(
        probed.reject_reason.value for probed in diagnostics if probed.reject_reason is not None
    )
    metrics = Layer03ExpansionMetrics(
        rim_anchor_count=len(anchors),
        seed_projection_attempt_count=seed_projection_attempts,
        local_geometry_rejected_count=geometry_rejected,
        route_probe_attempt_count=route_probe_attempts,
        route_probe_succeeded_count=len(normal),
        route_probe_failed_count=route_probe_attempts - len(normal),
        dedupe_duplicate_count=0,
        normal_candidate_count=len(normal),
        diagnostic_rejected_count=len(diagnostics),
        budget_skipped_count=0,
        layer_skip_reason=Layer03SkipReason.NONE,
        reject_reason_counts=tuple(sorted(reject_counts.items())),
    )
    observability = build_layer03_observability(
        metrics=metrics,
        normal_candidates=tuple(normal),
    )
    return build_rim_bundle_candidate_set(
        normal_candidates=tuple(normal),
        diagnostic_rejected_candidates=tuple(diagnostics),
        metrics=metrics,
        observability=observability,
    )


__all__ = [
    "generate_candidates",
    "output_dir_rank",
    "rotate_offset_east_to",
]
