"""Route probe tests (Solver Runtime PR2)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.enums import (
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import project_gene_placement
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    ExistingTransportCell,
    RouteGoal,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_domain import RouteDomainSnapshotBuilder
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)


def _open_void_input(*, bb: BBox | None = None):
    bb = bb or BBox(0, 4, 0, 4)
    void = frozenset(
        (sx, sy)
        for sx in range(bb.min_sx, bb.max_sx + 1)
        for sy in range(bb.min_sy, bb.max_sy + 1)
    )
    return replace(greenfield_optimization_input(bbox=bb), external_void_cells=void)


def test_route_probe_reaches_goal_on_open_domain() -> None:
    inp = _open_void_input()
    goal = RouteGoal(
        coord=(4, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = replace(inp, route_goals=frozenset({goal}))
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 0),
        goals=inp.route_goals,
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=200,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    result = run_route_probe(probe)
    assert result.reachable is True
    assert result.reached_goal == goal
    assert result.path[0] == (0, 0)
    assert result.path[-1] == (4, 0)


def test_route_probe_returns_no_goal_cells_when_filtered_goals_empty() -> None:
    inp = _open_void_input()
    goal = RouteGoal(
        coord=(4, 4),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.FLUID_PIPE,
        priority=10,
        existing_trunk=False,
    )
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 0),
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=50,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    result = run_route_probe(probe)
    assert result.reachable is False
    assert result.failure_reason == RouteProbeFailureReason.NO_GOAL_CELLS


def test_route_probe_respects_hard_blocked_cells() -> None:
    inp = _open_void_input()
    blocked = frozenset({(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)})
    inp = replace(inp, blocked_cells=blocked)
    goal = RouteGoal(
        coord=(4, 2),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 2),
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=500,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    result = run_route_probe(probe)
    assert result.reachable is False
    assert (1, 2) not in result.path


def test_route_probe_respects_transport_mask() -> None:
    bb = BBox(0, 3, 0, 0)
    transport = frozenset(
        {
            ExistingTransportCell(coord=(1, 0), transport_kind=TransportKind.SHAPE_BELT),
        }
    )
    inp = replace(
        greenfield_optimization_input(bbox=bb),
        existing_transport_cells=transport,
    )
    goal = RouteGoal(
        coord=(3, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.FLUID_PIPE,
        priority=5,
        existing_trunk=False,
    )
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 0),
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=50,
        transport_kind=TransportKind.FLUID_PIPE,
    )
    result = run_route_probe(probe)
    assert result.reachable is False


def test_route_probe_budget_exceeded() -> None:
    inp = _open_void_input(bb=BBox(0, 10, 0, 0))
    goal = RouteGoal(
        coord=(10, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 0),
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=1,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    result = run_route_probe(probe)
    assert result.reachable is False
    assert result.failure_reason == RouteProbeFailureReason.BUDGET_EXCEEDED


def test_route_probe_selects_goal_by_priority_weighted_score() -> None:
    inp = _open_void_input(bb=BBox(0, 2, 0, 2))
    low_pri = RouteGoal(
        coord=(2, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=5,
        existing_trunk=False,
    )
    high_pri = RouteGoal(
        coord=(0, 2),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=50,
        existing_trunk=False,
    )
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    probe = RouteProbeInput(
        start=(0, 0),
        goals=frozenset({low_pri, high_pri}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=50,
        transport_kind=TransportKind.SHAPE_BELT,
        goal_priority_weight=10,
    )
    result = run_route_probe(probe)
    assert result.reachable is True
    assert result.reached_goal == low_pri


def test_route_probe_uses_route_probe_start_not_fixed_output_transport() -> None:
    from pathlib import Path

    from django_apps.asteroid_lab.optimization.enums import Direction
    from django_apps.asteroid_lab.optimization.gene_template_loader import (
        load_gene_templates_from_json,
    )

    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"
    gene = load_gene_templates_from_json(fixture / "minimal_extractor_e.json")[0]

    bb = BBox(0, 6, 0, 0)
    mineable = frozenset({(0, 0)})
    void = frozenset((sx, 0) for sx in range(bb.min_sx, bb.max_sx + 1))
    inp = replace(
        greenfield_optimization_input(bbox=bb),
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=mineable,
        external_void_cells=void,
    )
    projected = project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
    goal = RouteGoal(
        coord=(5, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    domain = build_route_domain_for_projected_gene_probe(inp, projected)
    assert domain[projected.fixed_output_transport].hard_blocked is True

    probe = RouteProbeInput(
        start=projected.route_probe_start,
        goals=frozenset({goal}),
        route_domain=domain,
        topology_graph=inp.topology_graph,
        max_expansions=100,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    result = run_route_probe(probe)
    assert result.reachable is True
    assert result.path[0] == projected.route_probe_start
    assert projected.fixed_output_transport not in result.path
