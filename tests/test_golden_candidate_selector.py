"""Golden regression: OD-3 trunk-split selection order (Phase 2 harness)."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_selector import select_gene_candidates_greedy
from django_apps.asteroid_lab.optimization.enums import Direction, RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    RouteGoal,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult
from harness.validators.compare_golden import assert_golden_match, golden_path

GOLDEN_NAME = "candidate_selector_trunk_split"


def _gene_from_row(row: dict) -> GeneCandidate:
    coord = tuple(row["goal_coord"])
    kind = TransportKind(row["transport_kind"])
    extractor = tuple(row.get("extractor", [0, 0]))
    goal = RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=kind,
        priority=int(row["goal_priority"]),
        existing_trunk=False,
    )
    probe = RouteProbeResult(
        reachable=True,
        path=(),
        cost=int(row["cost"]),
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=int(row["goal_priority"]),
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=str(row["candidate_id"]),
        gene_id="golden",
        topology_signature="sig",
        extractor=extractor,
        extensions=(),
        occupied_cells=frozenset({extractor}),
        route_probe_start=(extractor[0] + 2, extractor[1]),
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=kind,
        base_throughput=int(row["base_throughput"]),
        base_score=float(row["base_throughput"]),
        route_probe_result=probe,
    )


@pytest.mark.unit
def test_golden_candidate_selector_trunk_split_order() -> None:
    payload = json.loads(golden_path(GOLDEN_NAME, kind="input").read_text(encoding="utf-8"))
    rows = payload["candidates"]
    candidates = tuple(_gene_from_row(r) for r in rows)
    goals = frozenset(c.route_probe_result.reached_goal for c in candidates)
    inp = replace(
        greenfield_optimization_input(bbox=BBox(0, 10, 0, 0)),
        route_goals=goals,
    )
    plan, _diag = select_gene_candidates_greedy(candidates, inp=inp)
    actual = {"ordered_candidate_ids": list(plan.ordered_candidate_ids)}
    assert_golden_match(actual, golden_path(GOLDEN_NAME, kind="expected"))
