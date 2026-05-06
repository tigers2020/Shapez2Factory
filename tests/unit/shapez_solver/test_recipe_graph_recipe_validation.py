"""Tests for recipe_graph_recipe_validation."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_solver.services.recipe_graph_recipe_validation import (
    annotate_visual_graph_with_issues,
    validate_recipe_graph_context,
)


def test_validate_no_target_info() -> None:
    doc = {
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
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    codes = {i["code"] for i in issues}
    assert "no_target_node" in codes


def test_validate_target_empty_warning() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "target_shape_empty" for i in issues)
    assert not any(i["severity"] == "error" for i in issues)


def test_validate_target_signature_match() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert not any(i["code"] == "target_signature_mismatch" for i in issues)


def test_validate_target_signature_mismatch_error() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "RcRcCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "target_signature_mismatch" for i in issues)
    assert any(i["severity"] == "error" for i in issues)


def test_validate_target_geometric_rotation_matches_family() -> None:
    """RuSuSuCu raw letter-sig ABBC, but quadrant rotation includes ABCC (Pattern Lab)."""
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "RuSuSuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=True,
        graph_document=doc,
    )
    assert not any(i["code"] == "target_signature_mismatch" for i in issues)


def test_validate_target_strict_inventory_without_rotation() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "RuSuSuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "target_signature_mismatch" for i in issues)


def test_validate_quantity_bool_error() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": True,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "shape_quantity_type" for i in issues)


def test_validate_multi_layer_source_ok() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "WrCrRgSy:RcRcRrRr",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert not any(i["code"] == "shape_code_invalid" for i in issues)


def test_validate_shape_code_too_many_layers_error() -> None:
    five = ":".join(["CuCuCuCu"] * 5)
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": five,
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "shape_code_invalid" for i in issues)
    assert any("layers" in i["message"] for i in issues)


def test_validate_multi_layer_target_family_per_layer() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuCuCuCu:CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="AAAA",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert not any(i["severity"] == "error" for i in issues)


def test_validate_multi_layer_target_family_mismatch_second_layer() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuCuCuCu:RcRcCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    issues = validate_recipe_graph_context(
        family_signature="AAAA",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "target_signature_mismatch" for i in issues)
    assert any("layer 1" in i["message"] for i in issues)


def test_validate_multi_output_operation_warns_missing_edges() -> None:
    doc = {
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
            {"id": "o1", "kind": "operation", "operation": "cutter", "x": 100, "y": 0},
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
        ],
    }
    issues = validate_recipe_graph_context(
        family_signature="ABCC",
        family_allow_rotation=False,
        graph_document=doc,
    )
    assert any(i["code"] == "operation_output_edges" for i in issues)


def test_annotate_visual_graph_marks_error_node() -> None:
    visual: dict[str, Any] = {
        "layout": {"direction": "horizontal"},
        "nodes": [
            {"id": "a", "kind": "shape", "role": "target"},
            {"id": "b", "kind": "shape", "role": "source"},
        ],
        "edges": [],
    }
    issues = [
        {
            "severity": "error",
            "code": "x",
            "message": "m",
            "node_ids": ["a"],
        },
    ]
    annotate_visual_graph_with_issues(visual, issues)
    assert visual["nodes"][0].get("validation_severity") == "error"
    assert "validation_severity" not in visual["nodes"][1]
