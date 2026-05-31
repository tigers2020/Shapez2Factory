"""Layer 03 Phase D — commit-time re-probe + provisional result assembly.

The beam selector (Phase C1) chooses a non-conflicting subset of the route-feasible normal
pool, but its per-candidate route probes were run in isolation against the *empty* field.
Phase D re-probes the chosen bundles **in selection order on the latest route domain**: each
commit adds its equipment as a hard blocker and its route path as a reserved corridor, so a
later bundle whose only route would cross an already-committed corridor is dropped (candidate
reachability is never the final commit proof — spec D/forbidden shortcuts). Survivors become
provisional ``committed_placements``; this layer still commits nothing downstream (L5/L6 own
interior fill and final mutation).
"""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    BundleCellRole,
    RouteProbedBundleCandidate,
    RouteProbeStatus,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    RimGreedyMetrics,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPass2Report,
    RimGreedyReject,
    RimGreedyRejectReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    LAYER_03_APPEND_SOURCE,
    AppendCellKind,
    AppendedPlacementCell,
    Layer03AppendResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.beam_selector import (  # noqa: E501
    BeamSelectionResult,
)
from shapez2_factory.application.asteroid_lab.layers.shared.route_probe import weighted_route_probe
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, bbox_from_coords
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (  # noqa: E501
    ReconstructionCompleteMap,
)


@dataclass(frozen=True, slots=True)
class FinalizeResult:
    committed_placements: tuple[CommittedRimSeedPlacement, ...]
    rejected_attempts: tuple[RimGreedyReject, ...]
    occupied_equipment_cells: frozenset[Coord]
    reserved_route_cells: frozenset[Coord]


def _cells_for_role(probed: RouteProbedBundleCandidate, role: BundleCellRole) -> frozenset[Coord]:
    return frozenset(p.coord for p in probed.candidate.placements if p.cell_role is role)


def _build_route_goals(exterior_plan: ExteriorConnectionPlan) -> tuple[RouteGoal, ...]:
    return build_layer03_route_goals(
        exterior_plan, transport_kind=TransportKind.SHAPE_BELT
    ) + build_layer03_route_goals(exterior_plan, transport_kind=TransportKind.FLUID_PIPE)


def finalize_selection(
    *,
    selected: tuple[RouteProbedBundleCandidate, ...],
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan,
) -> FinalizeResult:
    """Re-probe the selected bundles in order on the cumulatively-blocked route domain.

    Each surviving commit blocks its equipment and reserves its route path for subsequent
    re-probes, so corridor conflicts that the isolated Phase B probes could not see now drop
    the later bundle (``ROUTE_CROSSES_HARD_BLOCKER`` / ``DPS_UNREACHABLE``).
    """

    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    base_walkable = field_cells | external_void
    if not base_walkable or not selected:
        return FinalizeResult(
            committed_placements=(),
            rejected_attempts=(),
            occupied_equipment_cells=frozenset(),
            reserved_route_cells=frozenset(),
        )
    search_bbox = bbox_from_coords(base_walkable)
    route_goals = _build_route_goals(exterior_plan)

    committed_equipment: set[Coord] = set()
    reserved_route: set[Coord] = set()
    committed: list[CommittedRimSeedPlacement] = []
    rejects: list[RimGreedyReject] = []

    for probed in selected:
        cand = probed.candidate
        own_equipment = cand.mining_occupied_cells | cand.transport_stub_cells
        # Hard blockers for this re-probe: prior committed equipment + reserved corridors +
        # this bundle's own equipment (a belt may not route through its own miner).
        if committed_equipment & set(own_equipment):
            rejects.append(_reject(cand, RimGreedyRejectReason.EQUIPMENT_COLLISION))
            continue
        blockers = committed_equipment | reserved_route | set(own_equipment)
        walkable = base_walkable - blockers
        field_cost = field_cells - blockers
        domain = WeightedTransportRouteDomain(
            search_bbox=search_bbox,
            blocked_cells=frozenset(blockers),
            walkable_cells=walkable,
            field_cost_cells=field_cost,
        )
        reprobed = weighted_route_probe(
            candidate=cand,
            route_goals=route_goals,
            domain=domain,
            field_cells=field_cells,
        )
        if reprobed.route_probe_status != RouteProbeStatus.SUCCEEDED or (
            reprobed.route_probe_result is None
        ):
            rejects.append(_reject(cand, RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER))
            continue
        path = reprobed.route_probe_result.path_coords
        committed_equipment |= set(own_equipment)
        reserved_route |= set(path) - set(own_equipment)
        committed.append(_committed_placement(probed, path))

    return FinalizeResult(
        committed_placements=tuple(committed),
        rejected_attempts=tuple(rejects),
        occupied_equipment_cells=frozenset(committed_equipment),
        reserved_route_cells=frozenset(reserved_route),
    )


def _reject(cand: BundleCandidate, reason: RimGreedyRejectReason) -> RimGreedyReject:
    return RimGreedyReject(
        anchor=cand.anchor_coord,
        variant_id=cand.candidate_id,
        output_dir=cand.output_dir.value,
        seed_id=cand.gene_key,
        reason=reason,
    )


def _committed_placement(
    probed: RouteProbedBundleCandidate,
    path: tuple[Coord, ...],
) -> CommittedRimSeedPlacement:
    cand = probed.candidate
    miner_cells = _cells_for_role(probed, BundleCellRole.MINER)
    extension_cells = _cells_for_role(probed, BundleCellRole.EXTENSION)
    stub_cells = _cells_for_role(probed, BundleCellRole.TRANSPORT_STUB)
    stub = next(iter(stub_cells)) if stub_cells else cand.route_probe_start_coord
    return CommittedRimSeedPlacement(
        placement_id=cand.candidate_id,
        variant_id=cand.topology_signature,
        anchor=cand.anchor_coord,
        output_dir=cand.output_dir.value,
        seed_id=cand.gene_key,
        miner_cells=miner_cells,
        extension_cells=extension_cells,
        m_output_stub=stub,
        route_probe_path=path,
    )


def _build_overlay(
    committed: tuple[CommittedRimSeedPlacement, ...],
) -> ProvisionalLayoutOverlay:
    if not committed:
        return ProvisionalLayoutOverlay.empty()
    by_cell: dict[Coord, ProvisionalPlacedCell] = {}
    extractor: set[Coord] = set()
    extension: set[Coord] = set()
    stub: set[Coord] = set()
    for placement in committed:
        _add_cells(by_cell, extractor, placement.miner_cells, placement, BundleCellRole.MINER)
        _add_cells(
            by_cell, extension, placement.extension_cells, placement, BundleCellRole.EXTENSION
        )
        _add_cells(
            by_cell, stub, {placement.m_output_stub}, placement, BundleCellRole.TRANSPORT_STUB
        )
    occupied = set(by_cell.keys())
    return ProvisionalLayoutOverlay(
        occupied_cells=frozenset(occupied),
        extractor_cells=frozenset(extractor),
        extension_cells=frozenset(extension),
        transport_stub_cells=frozenset(stub),
        by_cell=by_cell,
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


def _add_cells(
    by_cell: dict[Coord, ProvisionalPlacedCell],
    bucket: set[Coord],
    cells: frozenset[Coord] | set[Coord],
    placement: CommittedRimSeedPlacement,
    role: BundleCellRole,
) -> None:
    for coord in cells:
        bucket.add(coord)
        by_cell[coord] = ProvisionalPlacedCell(
            coord=coord,
            candidate_id=placement.placement_id,
            placement_id=placement.placement_id,
            role=role,
            transport_kind=TransportKind.SHAPE_BELT,
            placement_state=PlacementCommitState.PROVISIONAL_PLACED,
        )


def _build_append_result(
    committed: tuple[CommittedRimSeedPlacement, ...],
    reserved_route: frozenset[Coord],
) -> Layer03AppendResult:
    cells: list[AppendedPlacementCell] = []
    for placement in committed:
        for coord in sorted(placement.miner_cells):
            cells.append(_append_cell(coord, AppendCellKind.MINER, placement))
        for coord in sorted(placement.extension_cells):
            cells.append(_append_cell(coord, AppendCellKind.EXTENSION, placement))
        cells.append(_append_cell(placement.m_output_stub, AppendCellKind.OUTPUT_STUB, placement))
    equipment = {
        coord
        for placement in committed
        for coord in (*placement.miner_cells, *placement.extension_cells, placement.m_output_stub)
    }
    for coord in sorted(reserved_route - equipment):
        cells.append(
            AppendedPlacementCell(
                coord=coord,
                kind=AppendCellKind.ROUTE_RESERVED,
                placement_id="route_reserved",
                variant_id="route_reserved",
                source_layer=LAYER_03_APPEND_SOURCE,
            )
        )
    return Layer03AppendResult(
        cells=tuple(cells),
        placement_count=len(committed),
        route_reserved_cell_count=len(reserved_route - equipment),
        source_layer=LAYER_03_APPEND_SOURCE,
    )


def _append_cell(
    coord: Coord,
    kind: AppendCellKind,
    placement: CommittedRimSeedPlacement,
) -> AppendedPlacementCell:
    return AppendedPlacementCell(
        coord=coord,
        kind=kind,
        placement_id=placement.placement_id,
        variant_id=placement.variant_id,
        source_layer=LAYER_03_APPEND_SOURCE,
    )


def build_integrated_rim_greedy_result(
    *,
    finalize: FinalizeResult,
    selection: BeamSelectionResult,
    rim_anchor_count: int,
) -> IntegratedRimGreedyResult:
    """Assemble the canonical L3 result DTO from the finalized commit-time re-probe."""

    committed = finalize.committed_placements
    winning_variant_id = committed[0].variant_id if committed else ""
    total_route_length = sum(len(p.route_probe_path) for p in committed)
    miner_count = sum(len(p.miner_cells) for p in committed)
    extension_count = sum(len(p.extension_cells) for p in committed)
    pass2_score = float(selection.total_throughput) if committed else None
    pass2 = RimGreedyPass2Report(
        variant_id=winning_variant_id,
        score=pass2_score,
        hard_fail=not committed,
        miner_count=miner_count,
        extension_count=extension_count,
        total_route_length=total_route_length,
    )
    metrics = RimGreedyMetrics(
        rim_anchor_count=rim_anchor_count,
        committed_placement_count=len(committed),
        rejected_attempt_count=len(finalize.rejected_attempts),
        reserved_route_cell_count=len(finalize.reserved_route_cells),
        winning_variant_id=winning_variant_id,
        pass2_score=pass2_score,
        layer_skip_reason=None,
    )
    return IntegratedRimGreedyResult(
        committed_placements=committed,
        rejected_attempts=finalize.rejected_attempts,
        occupied_equipment_cells=finalize.occupied_equipment_cells,
        reserved_route_cells=finalize.reserved_route_cells,
        append_result=_build_append_result(committed, finalize.reserved_route_cells),
        provisional_overlay=_build_overlay(committed),
        pass2_report=pass2,
        winning_variant_id=winning_variant_id,
        metrics=metrics,
        observability_events=_observability_events(committed, rim_anchor_count),
    )


def _observability_events(
    committed: tuple[CommittedRimSeedPlacement, ...],
    rim_anchor_count: int,
) -> tuple[RimGreedyObservationEvent, ...]:
    payload = {
        "rim_anchor_count": rim_anchor_count,
        "committed_placement_count": len(committed),
    }
    events: list[RimGreedyObservationEvent] = [
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_BEGIN,
            variant_id="",
            payload=payload,
        )
    ]
    for placement in committed:
        events.append(
            RimGreedyObservationEvent(
                phase=RimGreedyObservationPhase.RIM_SEED_COMMITTED,
                variant_id=placement.variant_id,
                payload={"anchor": placement.anchor, "output_dir": placement.output_dir},
            )
        )
    events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_COMPLETE,
            variant_id="",
            payload=payload,
        )
    )
    return tuple(events)


__all__ = [
    "FinalizeResult",
    "build_integrated_rim_greedy_result",
    "finalize_selection",
]
