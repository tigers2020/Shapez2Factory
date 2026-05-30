"""Pass 1 — greedy provisional rim placement with route reservation."""

from __future__ import annotations

from dataclasses import dataclass, field

from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCellRole,
    RouteProbedBundleCandidate,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
    ProvisionalPlacedCell,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
    CommittedRimSeedPlacement,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPolicy,
    RimGreedyReject,
    RimGreedyRejectReason,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.dps_policy import (
    build_greedy_route_domain,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
    GreedyMinerSeed,
    sort_seeds_by_priority,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.local_window import (
    compute_greedy_search_bbox,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchors import RimAnchor
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.seed_orient import (
    SeedLayout,
    layout_seed_at_anchor,
)
from django_apps.asteroid_lab.layers.shared.route_probe import weighted_route_probe
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


@dataclass
class RimGreedyState:
    variant_id: str
    committed_placements: list[CommittedRimSeedPlacement] = field(default_factory=list)
    occupied_equipment_cells: set[Coord] = field(default_factory=set)
    reserved_route_cells: set[Coord] = field(default_factory=set)
    consumed_anchor_cells: set[Coord] = field(default_factory=set)
    invalidated_anchor_cells: set[Coord] = field(default_factory=set)
    rejected_attempts: list[RimGreedyReject] = field(default_factory=list)
    observability_events: list[RimGreedyObservationEvent] = field(default_factory=list)


def _reject(
    state: RimGreedyState,
    *,
    anchor: Coord,
    output_dir: str | None,
    seed_id: str | None,
    reason: RimGreedyRejectReason,
    detail: str = "",
) -> None:
    state.rejected_attempts.append(
        RimGreedyReject(
            anchor=anchor,
            variant_id=state.variant_id,
            output_dir=output_dir,
            seed_id=seed_id,
            reason=reason,
            detail=detail,
        )
    )
    state.observability_events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_SEED_ATTEMPT_REJECTED,
            variant_id=state.variant_id,
            payload={
                "anchor": anchor,
                "output_dir": output_dir,
                "seed_id": seed_id,
                "reason": reason.value,
                "detail": detail,
            },
        )
    )


def _refresh_invalidated_anchors(
    state: RimGreedyState,
    all_anchor_coords: frozenset[Coord],
) -> None:
    for coord in all_anchor_coords:
        if coord in state.consumed_anchor_cells:
            continue
        if coord in state.occupied_equipment_cells or coord in state.reserved_route_cells:
            state.invalidated_anchor_cells.add(coord)


def probe_seed_route(
    layout: SeedLayout,
    seed: GreedyMinerSeed,
    *,
    route_goals: tuple[RouteGoal, ...],
    complete_map: ReconstructionCompleteMap,
    search_bbox_margin: int,
    occupied_equipment: frozenset[Coord],
    transport_kind: TransportKind,
) -> RouteProbedBundleCandidate:
    goal_coords = frozenset(g.coord for g in route_goals)
    search_bbox = compute_greedy_search_bbox(
        equipment_cells=layout.equipment_cells,
        stub_cells=layout.transport_stub_cells,
        goal_coords=goal_coords,
        margin=search_bbox_margin,
    )
    domain = build_greedy_route_domain(
        complete_map=complete_map,
        search_bbox=search_bbox,
        occupied_equipment_cells=occupied_equipment,
    )
    candidate = make_bundle_candidate_for_test(
        gene_key=seed.seed_id,
        intrinsic_priority_rank=seed.intrinsic_priority_rank,
        anchor_coord=layout.anchor,
        output_dir=layout.direction,
        rotation=layout.rotation,
        mining_occupied_cells=layout.miner_cells,
        transport_stub_cells=layout.transport_stub_cells,
        route_probe_start_coord=layout.m_output_stub,
        transport_kind=transport_kind,
    )
    return weighted_route_probe(
        candidate=candidate,
        route_goals=route_goals,
        domain=domain,
        field_cells=complete_map.field_cells,
    )


def _path_crosses_hard_blocker(
    path: tuple[Coord, ...],
    *,
    occupied_equipment: frozenset[Coord],
) -> bool:
    return bool(set(path) & occupied_equipment)


def run_pass1_for_variant(
    *,
    variant_id: str,
    variant_anchors: tuple[RimAnchor, ...],
    seeds: tuple[GreedyMinerSeed, ...],
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    policy: RimGreedyPolicy,
    transport_kind: TransportKind,
) -> RimGreedyState:
    state = RimGreedyState(variant_id=variant_id)
    all_anchor_coords = frozenset(a.coord for a in variant_anchors)
    sorted_seeds = sort_seeds_by_priority(seeds)

    state.observability_events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_BEGIN,
            variant_id=variant_id,
            payload={"anchor_count": len(variant_anchors)},
        )
    )

    placement_counter = 0
    for anchor in variant_anchors:
        if anchor.coord in state.consumed_anchor_cells:
            _reject(
                state,
                anchor=anchor.coord,
                output_dir=None,
                seed_id=None,
                reason=RimGreedyRejectReason.ANCHOR_ALREADY_CONSUMED,
            )
            continue
        if anchor.coord in state.invalidated_anchor_cells:
            _reject(
                state,
                anchor=anchor.coord,
                output_dir=None,
                seed_id=None,
                reason=RimGreedyRejectReason.ANCHOR_INVALIDATED,
            )
            continue

        for output_dir in anchor.void_dirs:
            for seed in sorted_seeds:
                layout_result = layout_seed_at_anchor(
                    seed_id=seed.seed_id,
                    anchor=anchor.coord,
                    output_dir=output_dir,
                    complete_map=complete_map,
                    extension_count=seed.extension_count,
                )
                if not isinstance(layout_result, SeedLayout):
                    _reject(
                        state,
                        anchor=anchor.coord,
                        output_dir=output_dir,
                        seed_id=seed.seed_id,
                        reason=layout_result.reason,
                        detail=layout_result.detail,
                    )
                    continue

                layout = layout_result
                if layout.equipment_cells & frozenset(state.occupied_equipment_cells):
                    _reject(
                        state,
                        anchor=anchor.coord,
                        output_dir=output_dir,
                        seed_id=seed.seed_id,
                        reason=RimGreedyRejectReason.EQUIPMENT_COLLISION,
                    )
                    continue
                if layout.equipment_cells & frozenset(state.reserved_route_cells):
                    _reject(
                        state,
                        anchor=anchor.coord,
                        output_dir=output_dir,
                        seed_id=seed.seed_id,
                        reason=RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER,
                        detail="equipment intersects reserved route",
                    )
                    continue

                occupied_frozen = frozenset(state.occupied_equipment_cells)
                probed = probe_seed_route(
                    layout,
                    seed,
                    route_goals=route_goals,
                    complete_map=complete_map,
                    search_bbox_margin=policy.dps_search_margin,
                    occupied_equipment=occupied_frozen,
                    transport_kind=transport_kind,
                )
                if probed.route_probe_status is not RouteProbeStatus.SUCCEEDED:
                    _reject(
                        state,
                        anchor=anchor.coord,
                        output_dir=output_dir,
                        seed_id=seed.seed_id,
                        reason=RimGreedyRejectReason.DPS_UNREACHABLE,
                    )
                    continue

                assert probed.route_probe_result is not None
                path = probed.route_probe_result.path_coords
                if _path_crosses_hard_blocker(path, occupied_equipment=occupied_frozen):
                    _reject(
                        state,
                        anchor=anchor.coord,
                        output_dir=output_dir,
                        seed_id=seed.seed_id,
                        reason=RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER,
                    )
                    continue

                placement_id = f"rim_greedy_{variant_id}_{placement_counter}"
                placement_counter += 1
                committed = CommittedRimSeedPlacement(
                    placement_id=placement_id,
                    variant_id=variant_id,
                    anchor=layout.anchor,
                    output_dir=layout.output_dir,
                    seed_id=seed.seed_id,
                    miner_cells=layout.miner_cells,
                    extension_cells=layout.extension_cells,
                    m_output_stub=layout.m_output_stub,
                    route_probe_path=path,
                )
                state.committed_placements.append(committed)
                state.occupied_equipment_cells |= layout.equipment_cells
                state.reserved_route_cells |= set(path)
                for coord in all_anchor_coords:
                    if coord in layout.equipment_cells:
                        state.consumed_anchor_cells.add(coord)
                _refresh_invalidated_anchors(state, all_anchor_coords)
                state.observability_events.append(
                    RimGreedyObservationEvent(
                        phase=RimGreedyObservationPhase.RIM_SEED_COMMITTED,
                        variant_id=variant_id,
                        payload={
                            "placement_id": placement_id,
                            "anchor": anchor.coord,
                            "seed_id": seed.seed_id,
                        },
                    )
                )
                break

    state.observability_events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_PASS1_COMPLETE,
            variant_id=variant_id,
            payload={"committed_count": len(state.committed_placements)},
        )
    )
    return state


def build_provisional_overlay_from_state(
    state: RimGreedyState,
    *,
    transport_kind: TransportKind,
) -> ProvisionalLayoutOverlay:
    by_cell: dict[Coord, ProvisionalPlacedCell] = {}
    for placement in state.committed_placements:
        for coord in placement.miner_cells:
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=placement.seed_id,
                placement_id=placement.placement_id,
                role=BundleCellRole.MINER,
                transport_kind=transport_kind,
                placement_state=PlacementCommitState.PROVISIONAL_PLACED,
            )
        for coord in placement.extension_cells:
            by_cell[coord] = ProvisionalPlacedCell(
                coord=coord,
                candidate_id=placement.seed_id,
                placement_id=placement.placement_id,
                role=BundleCellRole.EXTENSION,
                transport_kind=transport_kind,
                placement_state=PlacementCommitState.PROVISIONAL_PLACED,
            )
        by_cell[placement.m_output_stub] = ProvisionalPlacedCell(
            coord=placement.m_output_stub,
            candidate_id=placement.seed_id,
            placement_id=placement.placement_id,
            role=BundleCellRole.TRANSPORT_STUB,
            transport_kind=transport_kind,
            placement_state=PlacementCommitState.PROVISIONAL_PLACED,
        )

    occupied = frozenset(by_cell.keys())
    extractors = frozenset(c for c, cell in by_cell.items() if cell.role is BundleCellRole.MINER)
    extensions = frozenset(
        c for c, cell in by_cell.items() if cell.role is BundleCellRole.EXTENSION
    )
    stubs = frozenset(
        c for c, cell in by_cell.items() if cell.role is BundleCellRole.TRANSPORT_STUB
    )
    return ProvisionalLayoutOverlay(
        occupied_cells=occupied,
        extractor_cells=extractors,
        extension_cells=extensions,
        transport_stub_cells=stubs,
        by_cell=by_cell,
        source_layer=LAYER_03_GREEDY_SOURCE,
    )


__all__ = [
    "RimGreedyState",
    "build_provisional_overlay_from_state",
    "probe_seed_route",
    "run_pass1_for_variant",
]
