import pytest

from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document
from django_apps.shapez_solver.services.recipe_graph_topology import (
    assert_delivery_targets_unique,
    assert_recipe_graph_edge_topology,
)


def test_topology_allows_shape_op_intermediate_chain() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "s0", "kind": "shape", "role": "source", "shape_code": "Cu", "x": 0, "y": 0},
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 1, "y": 0},
            {"id": "i1", "kind": "shape", "role": "intermediate", "shape_code": "", "x": 2, "y": 0},
        ],
        "edges": [
            {"from": "s0", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "i1", "kind": "output", "slot": "0"},
        ],
    }
    out = validate_graph_document(doc)
    assert_recipe_graph_edge_topology(out)


def test_topology_rejects_output_to_target() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "s0", "kind": "shape", "role": "source", "shape_code": "Cu", "x": 0, "y": 0},
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 1, "y": 0},
            {"id": "t1", "kind": "shape", "role": "target", "shape_code": "", "x": 2, "y": 0},
        ],
        "edges": [
            {"from": "s0", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "t1", "kind": "output", "slot": "0"},
        ],
    }
    with pytest.raises(ValueError, match="intermediate"):
        validate_graph_document(doc)


def test_topology_rejects_operation_to_operation() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 0, "y": 0},
            {"id": "o2", "kind": "operation", "operation": "rotate_ccw", "x": 1, "y": 0},
        ],
        "edges": [
            {"from": "o1", "to": "o2", "kind": "input"},
        ],
    }
    with pytest.raises(ValueError, match="input edge must be shape"):
        validate_graph_document(doc)


def test_topology_allows_delivery_intermediate_to_target() -> None:
    doc = validate_graph_document(
        {
            "schema_version": 1,
            "nodes": [
                {
                    "id": "im",
                    "kind": "shape",
                    "role": "intermediate",
                    "shape_code": "",
                    "x": 0,
                    "y": 0,
                },
                {"id": "tgt", "kind": "shape", "role": "target", "shape_code": "", "x": 1, "y": 0},
            ],
            "edges": [{"from": "im", "to": "tgt", "kind": "delivery"}],
        },
    )
    assert_recipe_graph_edge_topology(doc)
    assert_delivery_targets_unique(doc["edges"])


def test_topology_rejects_duplicate_delivery_to_same_target() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "im1", "kind": "shape", "role": "intermediate", "shape_code": "", "x": 0, "y": 0},
            {"id": "im2", "kind": "shape", "role": "intermediate", "shape_code": "", "x": 1, "y": 0},
            {"id": "tgt", "kind": "shape", "role": "target", "shape_code": "", "x": 2, "y": 0},
        ],
        "edges": [
            {"from": "im1", "to": "tgt", "kind": "delivery"},
            {"from": "im2", "to": "tgt", "kind": "delivery"},
        ],
    }
    with pytest.raises(ValueError, match="duplicate delivery"):
        validate_graph_document(doc)


def test_topology_rejects_delivery_from_source_shape() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "s0", "kind": "shape", "role": "source", "shape_code": "Cu", "x": 0, "y": 0},
            {"id": "tgt", "kind": "shape", "role": "target", "shape_code": "", "x": 1, "y": 0},
        ],
        "edges": [{"from": "s0", "to": "tgt", "kind": "delivery"}],
    }
    with pytest.raises(ValueError, match="delivery source must be role=intermediate"):
        validate_graph_document(doc)
