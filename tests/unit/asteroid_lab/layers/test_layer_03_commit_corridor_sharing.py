"""L3 commit reprobe: void belt trunks are not hard-blocked (CANON 12:1 miner-to-belt)."""

from __future__ import annotations

import inspect
from decimal import Decimal

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
    commit_reprobe,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_finalize import (  # noqa: E501
    finalize_selection,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_reprobe import (  # noqa: E501
    CommitDomainState,
    build_commit_reprobe_context,
    try_commit_reprobe,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


def _corridor_sharing_complete_map() -> ReconstructionCompleteMap:
    """Two east-facing rim miners with a merge trunk at ``(5, 2)``."""

    field = frozenset({(1, 1), (1, 3)})
    void = frozenset(
        {
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            (5, 2),
        }
    )
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def _corridor_sharing_exterior_plan() -> ExteriorConnectionPlan:
    goal = (5, 2)
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="merge_goal",
                void_coord=goal,
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(goal,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def test_commit_reprobe_hard_blockers_are_equipment_only() -> None:
    """Regression: ``state.corridor`` must not appear in walkable blockers."""

    source = inspect.getsource(commit_reprobe.try_commit_reprobe)
    blockers_line = next(
        line for line in source.splitlines() if line.strip().startswith("blockers =")
    )
    assert blockers_line.strip() == "blockers = state.occupied | set(own_equipment)"
    assert "state.corridor" not in blockers_line


def _probed_miner(
    *,
    gene_key: str,
    anchor: Coord,
    path: tuple[Coord, ...],
    start: Coord,
    throughput: int = 8,
) -> RouteProbedBundleCandidate:
    stub = (anchor[0] + 1, anchor[1])
    probe_start = start
    candidate = make_bundle_candidate_for_test(
        gene_key=gene_key,
        anchor_coord=anchor,
        mining_occupied_cells=frozenset({anchor}),
        transport_stub_cells=frozenset({stub}),
        route_probe_start_coord=probe_start,
        throughput_factor=throughput,
    )
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=path[-1],
            path_coords=path,
            steps_expanded=len(path),
            transport_kind=TransportKind.SPACE_BELT,
            route_cost=len(path),
        ),
        route_goal_id="goal_0",
        reject_reason=None,
    )


def test_try_commit_reprobe_allows_shared_corridor_between_disjoint_equipment() -> None:
    """Two equipment-disjoint bundles may both commit when only the route corridor overlaps."""

    complete_map = _corridor_sharing_complete_map()
    exterior_plan = _corridor_sharing_exterior_plan()
    ctx = build_commit_reprobe_context(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert ctx is not None
    merge_tail = ((5, 1), (5, 2))
    first = _probed_miner(
        gene_key="north_rim",
        anchor=(1, 1),
        start=(3, 1),
        path=((3, 1), (4, 1), *merge_tail),
    )
    second = _probed_miner(
        gene_key="south_rim",
        anchor=(1, 3),
        start=(3, 3),
        path=((3, 3), (4, 3), (5, 3), (5, 2)),
    )
    state = CommitDomainState()
    ok_first, state_after_first, _ = try_commit_reprobe(
        ctx=ctx,
        state=state,
        probed=first,
    )
    ok_second, _state_after_second, _ = try_commit_reprobe(
        ctx=ctx,
        state=state_after_first,
        probed=second,
    )
    assert ok_first
    assert ok_second


def test_finalize_two_corridor_sharing_bundles_both_commit() -> None:
    complete_map = _corridor_sharing_complete_map()
    exterior_plan = _corridor_sharing_exterior_plan()
    merge_tail = ((5, 1), (5, 2))
    selected = (
        _probed_miner(
            gene_key="north_rim",
            anchor=(1, 1),
            start=(3, 1),
            path=((3, 1), (4, 1), *merge_tail),
        ),
        _probed_miner(
            gene_key="south_rim",
            anchor=(1, 3),
            start=(3, 3),
            path=((3, 3), (4, 3), (5, 3), (5, 2)),
        ),
    )
    finalize = finalize_selection(
        selected=selected,
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(finalize.committed_placements) == 2
    assert finalize.rejected_attempts == ()
