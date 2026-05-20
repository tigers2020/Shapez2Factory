"""Candidate equivalence key contract tests."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_equivalence import dedupe_gene_candidates
from django_apps.asteroid_lab.optimization.enums import Direction, RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult


def _candidate(
    *,
    candidate_id: str,
    occupied_cells: frozenset[tuple[int, int]],
    extractor: tuple[int, int],
) -> GeneCandidate:
    goal = RouteGoal(
        coord=(10, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    probe = RouteProbeResult(
        reachable=True,
        path=(),
        cost=1,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=10,
        failure_reason=None,
    )
    route_probe_start = (extractor[0] + 2, extractor[1])
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="same_gene",
        topology_signature="sig-a",
        extractor=extractor,
        extensions=(),
        occupied_cells=occupied_cells,
        route_probe_start=route_probe_start,
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=16,
        base_score=16.0,
        route_probe_result=probe,
    )


def test_dedupe_keeps_distinct_coords_same_pattern() -> None:
    c0 = _candidate(
        candidate_id="a:0,0:e:shape_belt",
        occupied_cells=frozenset({(0, 0), (1, 0)}),
        extractor=(0, 0),
    )
    c1 = _candidate(
        candidate_id="b:2,0:e:shape_belt",
        occupied_cells=frozenset({(2, 0), (3, 0)}),
        extractor=(2, 0),
    )
    c1 = replace(c1, topology_signature="sig-a")

    deduped = dedupe_gene_candidates((c0, c1))
    assert len(deduped) == 2
