from __future__ import annotations

from django_apps.shapez_solver.services.recipe_graph_react_flow_adapter import (
    REACT_FLOW_GRAPH_PAYLOAD_VERSION,
    domain_graph_to_react_flow,
    react_flow_to_domain_graph,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document


def test_domain_to_react_flow_empty_round_trip() -> None:
    doc = validate_graph_document({"schema_version": 1, "nodes": [], "edges": []})
    rf = domain_graph_to_react_flow(doc)
    assert rf["version"] == REACT_FLOW_GRAPH_PAYLOAD_VERSION
    assert rf["nodes"] == []
    assert rf["edges"] == []
    back = react_flow_to_domain_graph(rf)
    assert back == doc


def test_domain_to_react_flow_minimal_chain_round_trip() -> None:
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 100, "y": 0},
            {
                "id": "s2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "s2", "kind": "output"},
        ],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    assert [n["type"] for n in rf["nodes"]] == ["shape", "operation", "intermediate"]
    assert rf["edges"][0]["source"] == "s1"
    assert rf["edges"][0]["target"] == "o1"
    assert rf["edges"][0]["data"]["domainKind"] == "input"
    assert rf["edges"][0].get("targetHandle") == "in"
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    assert back == doc


def test_domain_to_react_flow_target_shape_node_type() -> None:
    """target 역할 shape는 React Flow 노드 type ``output`` 으로 매핑한다(엣지 없이 타입만 검증)."""
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "Ab",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "Cd",
                "quantity": 1,
                "x": 50,
                "y": 0,
            },
        ],
        "edges": [],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    types = {n["id"]: n["type"] for n in rf["nodes"]}
    assert types["s2"] == "intermediate"
    assert types["t1"] == "output"


def test_react_flow_round_trip_preserves_fractional_positions() -> None:
    """캔버스 드래그 좌표는 graph_document x,y에 보존된다(저장·재로드 정합)."""
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 10.25,
                "y": -3.5,
            },
        ],
        "edges": [],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    pos = next(n for n in rf["nodes"] if n["id"] == "s1")["position"]
    assert pos["x"] == 10.25
    assert pos["y"] == -3.5
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    s1 = next(n for n in back["nodes"] if n["id"] == "s1")
    assert s1["x"] == 10.25
    assert s1["y"] == -3.5


def test_domain_to_react_flow_two_output_source_handles() -> None:
    """다출력 연산은 React Flow ``sourceHandle``을 레인별로 나눈다."""
    raw = {
        "schema_version": 1,
        "nodes": [
            {"id": "o1", "kind": "operation", "operation": "cutter", "x": 0, "y": 0},
            {
                "id": "s1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 1,
                "y": 0,
            },
            {
                "id": "s2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 2,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "o1", "to": "s1", "kind": "output", "slot": "0"},
            {"from": "o1", "to": "s2", "kind": "output", "slot": "1"},
        ],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    out_edges = [e for e in rf["edges"] if e.get("data", {}).get("domainKind") == "output"]
    assert len(out_edges) == 2
    handles = {e.get("sourceHandle") for e in out_edges}
    assert handles == {"out", "out-1"}
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    assert back == doc


def test_domain_to_react_flow_delivery_edge_round_trip() -> None:
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "im",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "AbCdAbCd",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "tgt",
                "kind": "shape",
                "role": "target",
                "shape_code": "",
                "quantity": 1,
                "x": 1,
                "y": 0,
            },
        ],
        "edges": [{"from": "im", "to": "tgt", "kind": "delivery"}],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    dom_kinds = [e["data"].get("domainKind") for e in rf["edges"]]
    assert "delivery" in dom_kinds
    assert rf["edges"][0].get("sourceHandle") == "out"
    assert rf["edges"][0].get("targetHandle") == "in"
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    assert back["edges"][0]["kind"] == "delivery"


def test_react_flow_round_trip_preserves_source_carrier_fluid() -> None:
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "f1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    n0 = next(n for n in rf["nodes"] if n["id"] == "f1")
    assert n0["data"].get("source_carrier") == "fluid"
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    assert back["nodes"][0].get("source_carrier") == "fluid"


def test_domain_to_react_flow_binary_input_handles_follow_slot_not_list_order() -> None:
    """Painter 등 슬롯이 있는 입력은 edges 배열 순서와 무관하게 ``targetHandle``에 반영된다."""
    raw = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "f1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 1,
            },
            {"id": "p1", "kind": "operation", "operation": "painter", "x": 100, "y": 0},
        ],
        "edges": [
            {"from": "f1", "to": "p1", "kind": "input", "slot": "1"},
            {"from": "s1", "to": "p1", "kind": "input"},
        ],
    }
    doc = validate_graph_document(raw)
    rf = domain_graph_to_react_flow(doc)
    inp = [e for e in rf["edges"] if e.get("data", {}).get("domainKind") == "input"]
    assert len(inp) == 2
    by_src = {e["source"]: e for e in inp}
    assert by_src["f1"].get("targetHandle") == "in-1"
    assert by_src["s1"].get("targetHandle") is None or by_src["s1"].get("targetHandle") == "in"
    back = validate_graph_document(react_flow_to_domain_graph(rf))
    assert back == doc
