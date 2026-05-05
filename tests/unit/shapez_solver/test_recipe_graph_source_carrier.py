from __future__ import annotations

from typing import Any

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document


def _minimal_doc(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"schema_version": 1, "nodes": nodes, "edges": edges or []}


def test_validate_fluid_source_accepts_primary_red() -> None:
    doc = _minimal_doc(
        [
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
    )
    validate_graph_document(doc)


def test_validate_fluid_source_rejects_cyan_uniform() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "f1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CcCcCcCc",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
        ],
    )
    with pytest.raises(ValueError, match="fluid source allows only primary"):
        validate_graph_document(doc)


def test_validate_material_source_allows_cyan_uniform() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CcCcCcCc",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
    )
    validate_graph_document(doc)


def test_validate_fluid_intermediate_accepts_pure_fluid_secondary_color() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "x1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "CyCyCyCy",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
        ],
    )
    validate_graph_document(doc)


def test_validate_painter_paint_color_accepts_r() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "paint_color": "r",
                "x": 200,
                "y": 0,
            },
        ],
    )
    validate_graph_document(doc)


def test_validate_painter_paint_color_rejects_magenta() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "paint_color": "m",
                "x": 200,
                "y": 0,
            },
        ],
    )
    with pytest.raises(ValueError, match="painter paint_color must be one of"):
        validate_graph_document(doc)


def test_validate_invalid_source_carrier_string() -> None:
    doc = _minimal_doc(
        [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "source_carrier": "liquid",
                "x": 0,
                "y": 0,
            },
        ],
    )
    with pytest.raises(ValueError, match="invalid shape.source_carrier"):
        validate_graph_document(doc)
