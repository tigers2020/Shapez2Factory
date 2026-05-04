from django_apps.shapez_solver.services.graph_document_primitive_chain import (
    try_linear_operation_sequence,
)


def test_linear_sequence_empty() -> None:
    assert try_linear_operation_sequence({"schema_version": 1, "nodes": [], "edges": []}) == []


def test_linear_sequence_single_op() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [{"id": "o1", "kind": "operation", "operation": "rotate_cw"}],
        "edges": [],
    }
    assert try_linear_operation_sequence(doc) == ["rotate_cw"]


def test_linear_sequence_multi_op_returns_none() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "o1", "kind": "operation", "operation": "rotate_cw"},
            {"id": "o2", "kind": "operation", "operation": "rotate_ccw"},
        ],
        "edges": [],
    }
    assert try_linear_operation_sequence(doc) is None
