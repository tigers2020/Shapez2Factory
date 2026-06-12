"""Fixture-driven checks: Python matches ``recipe_connection_rule_scenarios.json``.

The same JSON is consumed by Vitest in ``frontend/recipe_graph_editor`` (see
``tests/recipeConnection.fixture.test.ts``) to guard TS ``recipeConnection`` /
``operationArity`` against drift from ``recipe_graph_input_carrier``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.recipe_graph_input_carrier import (
    expected_input_carriers,
    required_input_count,
    sorted_shape_input_edges_to_operation,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "recipe_connection_rule_scenarios.json"
)


@pytest.fixture(scope="module")
def scenarios() -> dict[str]:
    raw = _FIXTURE.read_text(encoding="utf-8")
    return cast(dict[str], json.loads(raw))


def test_fixture_required_input_and_carriers(scenarios: dict[str]) -> None:
    for row in scenarios["required_input_and_carriers"]:
        op_type = OperationType(str(row["op_type"]))
        op_node = dict(row.get("op_node") or {})
        want_count = int(row["required_input_count"])
        want_carriers = tuple(str(x) for x in row["expected_carriers"])
        got_count = required_input_count(op_type, op_node)
        got_carriers = expected_input_carriers(op_type, op_node)
        assert got_count == want_count, row["id"]
        assert got_carriers == want_carriers, row["id"]


def test_fixture_input_edge_sort(scenarios: dict[str]) -> None:
    for row in scenarios["input_edge_sort"]:
        node_by_id: dict[str, dict[str]] = {}
        for n in row["shape_nodes"]:
            nid = str(n["id"])
            node_by_id[nid] = {"id": nid, "kind": str(n["kind"])}
        input_edges: list[dict[str]] = []
        for e in row["input_edges"]:
            edge: dict[str] = {"from": str(e["from"]), "to": str(e["to"])}
            if "slot" in e and e["slot"] is not None:
                edge["slot"] = e["slot"]
            input_edges.append(edge)
        sorted_edges = sorted_shape_input_edges_to_operation(input_edges, node_by_id)
        got_order = [str(x["from"]) for x in sorted_edges]
        assert got_order == row["expected_from_order"], row["id"]
