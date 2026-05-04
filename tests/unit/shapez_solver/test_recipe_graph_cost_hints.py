from django_apps.shapez_solver.services.recipe_graph_cost_hints import graph_cost_hint_from_document


def test_graph_cost_hint_counts_ops_and_shapes() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {"id": "s1", "kind": "shape"},
            {"id": "o1", "kind": "operation", "operation": "cutter"},
            {"id": "o2", "kind": "operation", "operation": "stacker"},
        ],
        "edges": [],
    }
    h = graph_cost_hint_from_document(doc)
    assert h["operation_node_count"] == 2
    assert h["shape_node_count"] == 1
    assert h["estimated_stage_count"] == 2
    assert h["graph_operation_cost_sum_min"] == 2
