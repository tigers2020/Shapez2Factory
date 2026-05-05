from __future__ import annotations

from typing import Any

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document


def _doc(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": 1, "nodes": nodes, "edges": edges}


def test_validate_color_mixer_rejects_material_fluid_inputs() -> None:
    doc = _doc(
        [
            {
                "id": "a",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "b",
                "kind": "shape",
                "role": "source",
                "shape_code": "CgCgCgCg",
                "quantity": 1,
                "x": 0,
                "y": 1,
            },
            {
                "id": "m",
                "kind": "operation",
                "operation": OperationType.COLOR_MIXER.value,
                "x": 1,
                "y": 0,
            },
        ],
        [
            {"from": "a", "to": "m", "kind": "input"},
            {"from": "b", "to": "m", "kind": "input", "slot": "1"},
        ],
    )
    with pytest.raises(ValueError, match="must be fluid"):
        validate_graph_document(doc)


def test_validate_color_mixer_accepts_two_fluid_sources() -> None:
    doc = _doc(
        [
            {
                "id": "a",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
            {
                "id": "b",
                "kind": "shape",
                "role": "source",
                "shape_code": "CgCgCgCg",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 1,
            },
            {
                "id": "m",
                "kind": "operation",
                "operation": OperationType.COLOR_MIXER.value,
                "x": 1,
                "y": 0,
            },
        ],
        [
            {"from": "a", "to": "m", "kind": "input"},
            {"from": "b", "to": "m", "kind": "input", "slot": "1"},
        ],
    )
    validate_graph_document(doc)


def test_validate_rotate_rejects_fluid_source() -> None:
    doc = _doc(
        [
            {
                "id": "a",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
            {
                "id": "r",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 1,
                "y": 0,
            },
        ],
        [{"from": "a", "to": "r", "kind": "input"}],
    )
    with pytest.raises(ValueError, match="must be material"):
        validate_graph_document(doc)


def test_validate_painter_two_inputs_accepts_shape_on_default_port_first_in_file() -> None:
    """Carrier rules follow handle/slot, not sorted edge order (shape may precede fluid in JSON)."""

    doc = _doc(
        [
            {
                "id": "shape_mat",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "shape_fluid",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 1,
            },
            {
                "id": "p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "x": 1,
                "y": 0,
            },
        ],
        [
            {"from": "shape_mat", "to": "p", "kind": "input"},
            {"from": "shape_fluid", "to": "p", "kind": "input", "slot": "1"},
        ],
    )
    validate_graph_document(doc)


def test_validate_painter_two_inputs_rejects_material_on_fluid_port() -> None:
    doc = _doc(
        [
            {
                "id": "a",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCu----",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "b",
                "kind": "shape",
                "role": "source",
                "shape_code": "CgCgCgCg",
                "quantity": 1,
                "x": 0,
                "y": 1,
            },
            {
                "id": "p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "x": 1,
                "y": 0,
            },
        ],
        [
            {"from": "a", "to": "p", "kind": "input", "slot": "1"},
            {"from": "b", "to": "p", "kind": "input"},
        ],
    )
    with pytest.raises(ValueError, match="must be fluid"):
        validate_graph_document(doc)


def test_validate_painter_two_inputs_rejects_fluid_on_shape_port() -> None:
    doc = _doc(
        [
            {
                "id": "fluid_ok",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 0,
            },
            {
                "id": "fluid_bad",
                "kind": "shape",
                "role": "source",
                "shape_code": "CgCgCgCg",
                "quantity": 1,
                "source_carrier": "fluid",
                "x": 0,
                "y": 1,
            },
            {
                "id": "p",
                "kind": "operation",
                "operation": OperationType.PAINTER.value,
                "x": 1,
                "y": 0,
            },
        ],
        [
            {"from": "fluid_ok", "to": "p", "kind": "input", "slot": "1"},
            {"from": "fluid_bad", "to": "p", "kind": "input"},
        ],
    )
    with pytest.raises(ValueError, match="must be material"):
        validate_graph_document(doc)
