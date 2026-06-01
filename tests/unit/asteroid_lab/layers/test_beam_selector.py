"""Layer 03 Phase C1 ??deterministic beam selector over the route-feasible normal pool.

Covers spec Phase C1 (v2 MVP): a deterministic beam/greedy selector that maximizes
routed throughput minus route-cost and shared-corridor-pressure penalties, with equipment
overlap as a HARD constraint (never a penalty), and D2 (selection consults fitness/conflict
state, not merely the D1 enumeration order).
"""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.beam_selector import (  # noqa: E501
    FitnessBreakdown,
    select_bundles,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


def _probed(
    *,
    gene_key: str,
    anchor: Coord,
    mining: frozenset[Coord],
    stub: Coord,
    start: Coord,
    path: tuple[Coord, ...],
    throughput: int,
    route_cost: int = 0,
) -> RouteProbedBundleCandidate:
    candidate = make_bundle_candidate_for_test(
        gene_key=gene_key,
        anchor_coord=anchor,
        mining_occupied_cells=mining,
        transport_stub_cells=frozenset({stub}),
        route_probe_start_coord=start,
        throughput_factor=throughput,
    )
    result = RouteProbeResult(
        reached_goal=True,
        goal_coord=path[-1],
        path_coords=path,
        steps_expanded=len(path),
        transport_kind=TransportKind.SHAPE_BELT,
        route_cost=route_cost,
    )
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=result,
        route_goal_id="goal_0",
        reject_reason=None,
    )


def test_empty_pool_selects_nothing() -> None:
    result = select_bundles(())
    assert result.selected == ()
    assert result.total_throughput == 0
    assert result.rejected_overlap_count == 0


def test_disjoint_candidates_are_all_selected() -> None:
    # Two equipment-disjoint candidates with disjoint paths -> both commit.
    a = _probed(
        gene_key="a",
        anchor=(3, 3),
        mining=frozenset({(3, 3)}),
        stub=(4, 3),
        start=(5, 3),
        path=((5, 3), (6, 3)),
        throughput=8,
    )
    b = _probed(
        gene_key="b",
        anchor=(3, 8),
        mining=frozenset({(3, 8)}),
        stub=(4, 8),
        start=(5, 8),
        path=((5, 8), (6, 8)),
        throughput=8,
    )
    result = select_bundles((a, b))
    assert {p.candidate.gene_key for p in result.selected} == {"a", "b"}
    assert result.total_throughput == 16
    assert result.rejected_overlap_count == 0


def test_overlapping_equipment_is_hard_constraint_higher_throughput_wins() -> None:
    # Both candidates occupy the shared extractor (6,4): they cannot coexist. The selector
    # must commit exactly the higher-throughput m3e and reject m0e for overlap (hard).
    m3e = _probed(
        gene_key="m3e",
        anchor=(6, 4),
        mining=frozenset({(6, 4), (5, 4), (4, 4), (3, 4)}),
        stub=(7, 4),
        start=(8, 4),
        path=((8, 4),),
        throughput=16,
    )
    m0e = _probed(
        gene_key="m0e",
        anchor=(6, 4),
        mining=frozenset({(6, 4)}),
        stub=(7, 4),
        start=(8, 4),
        path=((8, 4),),
        throughput=4,
    )
    result = select_bundles((m3e, m0e))
    assert [p.candidate.gene_key for p in result.selected] == ["m3e"]
    assert result.total_throughput == 16
    assert result.rejected_overlap_count == 1


def test_selection_consults_fitness_not_d1_order_d2() -> None:
    # D2: a low-throughput candidate that sorts FIRST in D1 order (smaller anchor) must not
    # pre-empt a higher-throughput candidate it conflicts with. Selection order is by
    # fitness/conflict state, so the high-throughput bundle wins despite later D1 rank.
    low_first = _probed(
        gene_key="low",
        anchor=(1, 1),
        mining=frozenset({(1, 1), (2, 1)}),
        stub=(0, 1),
        start=(0, 2),
        path=((0, 2),),
        throughput=4,
    )
    high_later = _probed(
        gene_key="high",
        anchor=(2, 1),  # conflicts with low's (2,1) equipment cell
        mining=frozenset({(2, 1), (3, 1)}),
        stub=(4, 1),
        start=(5, 1),
        path=((5, 1),),
        throughput=16,
    )
    result = select_bundles((low_first, high_later))
    assert [p.candidate.gene_key for p in result.selected] == ["high"]
    assert result.rejected_overlap_count == 1


def test_shared_corridor_is_a_penalty_not_a_hard_constraint() -> None:
    # Equipment-disjoint candidates whose route paths share a corridor cell are BOTH
    # selectable (corridor sharing is a penalty), but the later one records the shared
    # corridor pressure in its fitness breakdown.
    a = _probed(
        gene_key="a",
        anchor=(3, 3),
        mining=frozenset({(3, 3)}),
        stub=(4, 3),
        start=(5, 3),
        path=((5, 3), (6, 3), (7, 3)),
        throughput=8,
    )
    b = _probed(
        gene_key="b",
        anchor=(3, 5),
        mining=frozenset({(3, 5)}),
        stub=(4, 5),
        start=(5, 5),
        path=((5, 5), (6, 3), (7, 3)),  # shares corridor cells (6,3),(7,3) with a
        throughput=8,
    )
    result = select_bundles((a, b))
    assert {p.candidate.gene_key for p in result.selected} == {"a", "b"}
    by_id = {f.candidate_id: f for f in result.fitness}
    shared = [f for f in result.fitness if f.shared_corridor_cells > 0]
    assert shared, "expected one bundle to record shared corridor pressure"
    assert max(f.shared_corridor_cells for f in result.fitness) == 2
    assert all(isinstance(f, FitnessBreakdown) for f in by_id.values())


def test_shared_corridor_does_not_double_count_throughput_by_cell_overlap() -> None:
    """§RC3: shared corridor cells add soft pressure only — not extra throughput_factor per cell."""

    throughput = 8
    a = _probed(
        gene_key="a",
        anchor=(3, 3),
        mining=frozenset({(3, 3)}),
        stub=(4, 3),
        start=(5, 3),
        path=((5, 3), (6, 3), (7, 3)),
        throughput=throughput,
    )
    b = _probed(
        gene_key="b",
        anchor=(3, 5),
        mining=frozenset({(3, 5)}),
        stub=(4, 5),
        start=(5, 5),
        path=((5, 5), (6, 3), (7, 3)),
        throughput=throughput,
    )
    result = select_bundles((a, b))
    assert {p.candidate.gene_key for p in result.selected} == {"a", "b"}
    shared_cells = max(f.shared_corridor_cells for f in result.fitness)
    assert shared_cells == 2
    assert result.total_throughput == 2 * throughput
    assert result.total_throughput != 2 * throughput + shared_cells


def test_selection_is_deterministic() -> None:
    m3e = _probed(
        gene_key="m3e",
        anchor=(6, 4),
        mining=frozenset({(6, 4), (5, 4), (4, 4), (3, 4)}),
        stub=(7, 4),
        start=(8, 4),
        path=((8, 4),),
        throughput=16,
    )
    m0e = _probed(
        gene_key="m0e",
        anchor=(6, 4),
        mining=frozenset({(6, 4)}),
        stub=(7, 4),
        start=(8, 4),
        path=((8, 4),),
        throughput=4,
    )
    first = select_bundles((m3e, m0e))
    second = select_bundles((m0e, m3e))  # input order swapped
    assert [p.candidate.candidate_id for p in first.selected] == [
        p.candidate.candidate_id for p in second.selected
    ]
