"""Test helpers for Layer 04 placement (not algorithm input)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    BundleCellRole,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    LAYER_04_SOURCE,
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
    RimBundlePlacement,
    build_layer04_rim_placement_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind


def succeeded_probe_at(
    anchor: tuple[int, int],
    *,
    rank: int = 1,
    gene_key: str = "miner_seed_m3e_01",
    equivalence_key: str = "equiv_a",
    mining: frozenset[tuple[int, int]] | None = None,
    transport: frozenset[tuple[int, int]] | None = None,
    goal: tuple[int, int] = (8, 4),
    output_dir: Direction = Direction.E,
    rotation: int | None = None,
    route_cost: int = 0,
    throughput_factor: int = 16,
) -> RouteProbedBundleCandidate:
    if rotation is None:
        rotation = {
            Direction.E: 0,
            Direction.S: 1,
            Direction.W: 2,
            Direction.N: 3,
        }[output_dir]
    stub_start = (anchor[0] + 1, anchor[1]) if transport is None else min(transport)
    candidate = make_bundle_candidate_for_test(
        gene_key=gene_key,
        intrinsic_priority_rank=rank,
        anchor_coord=anchor,
        equivalence_key=equivalence_key,
        output_dir=output_dir,
        rotation=rotation,
        mining_occupied_cells=mining or frozenset({anchor}),
        transport_stub_cells=transport or frozenset({stub_start}),
        route_probe_start_coord=stub_start,
        throughput_factor=throughput_factor,
    )
    path = (stub_start, goal)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal,
            path_coords=path,
            steps_expanded=len(path),
            transport_kind=TransportKind.SPACE_BELT,
            route_cost=route_cost,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )


def _cells_for_role(
    placements: tuple[object, ...],
    role: BundleCellRole,
) -> frozenset[Coord]:
    from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundlePlacement

    typed = tuple(p for p in placements if isinstance(p, BundlePlacement))
    return frozenset(p.coord for p in typed if p.cell_role is role)


def rim_bundle_placement_from_probe(entry: RouteProbedBundleCandidate) -> RimBundlePlacement:
    candidate = entry.candidate
    placements = candidate.placements
    extractor = _cells_for_role(placements, BundleCellRole.MINER)
    extension = _cells_for_role(placements, BundleCellRole.EXTENSION)
    output_stub = _cells_for_role(placements, BundleCellRole.TRANSPORT_STUB)
    occupied = candidate.mining_occupied_cells | candidate.transport_stub_cells

    goal_cells: frozenset[Coord] = frozenset()
    path_cells: tuple[Coord, ...] = ()
    if entry.route_probe_result is not None:
        if entry.route_probe_result.goal_coord is not None:
            goal_cells = frozenset({entry.route_probe_result.goal_coord})
        path_cells = entry.route_probe_result.path_coords

    return RimBundlePlacement(
        candidate_id=candidate.candidate_id,
        placement_id=f"{candidate.candidate_id}:prov",
        equivalence_key=candidate.equivalence_key,
        gene_key=candidate.gene_key,
        anchor_coord=candidate.anchor_coord,
        transport_kind=candidate.transport_kind,
        resource_kind=candidate.resource_kind,
        occupied_cells=occupied,
        extractor_cells=extractor,
        extension_cells=extension,
        output_stub_cells=output_stub,
        route_probe_goal_cells=goal_cells,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
        intrinsic_priority_rank=candidate.intrinsic_priority_rank,
        cell_placements=placements,
        probed_route_path_cells=path_cells,
    )


def provisional_overlay_from_placements(
    placements: tuple[RimBundlePlacement, ...],
) -> ProvisionalLayoutOverlay:
    if not placements:
        return ProvisionalLayoutOverlay.empty()

    by_cell: dict[Coord, ProvisionalPlacedCell] = {}
    extractor: set[Coord] = set()
    extension: set[Coord] = set()
    transport_stub: set[Coord] = set()
    occupied: set[Coord] = set()

    for placement in placements:
        candidate = placement.candidate_id
        placement_id = placement.placement_id
        transport_kind = placement.transport_kind
        state = placement.placement_state
        for coord in placement.extractor_cells:
            extractor.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement_id,
                role=BundleCellRole.MINER,
                transport_kind=transport_kind,
                placement_state=state,
            )
        for coord in placement.extension_cells:
            extension.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement_id,
                role=BundleCellRole.EXTENSION,
                transport_kind=transport_kind,
                placement_state=state,
            )
        for coord in placement.output_stub_cells:
            transport_stub.add(coord)
            occupied.add(coord)
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=candidate,
                placement_id=placement_id,
                role=BundleCellRole.TRANSPORT_STUB,
                transport_kind=transport_kind,
                placement_state=state,
            )

    return ProvisionalLayoutOverlay(
        occupied_cells=frozenset(occupied),
        extractor_cells=frozenset(extractor),
        extension_cells=frozenset(extension),
        transport_stub_cells=frozenset(transport_stub),
        by_cell=by_cell,
        source_layer=LAYER_04_SOURCE,
    )


def layer04_rim_placement_result_for_probes(
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> Layer04RimPlacementResult:
    placements = tuple(rim_bundle_placement_from_probe(e) for e in entries)
    return build_layer04_rim_placement_result(
        selected_placements=placements,
        rejected_candidates=(),
        provisional_overlay=provisional_overlay_from_placements(placements),
        replay_frames=(),
    )
