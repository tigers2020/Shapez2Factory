from typing import Any

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_semantics import apply_operation
from django_apps.shapez_solver.services.recipe_graph_constants import (
    RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING,
    RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    default_empty_graph_document,
    recompute_graph_document,
    recompute_validated_graph_document,
    try_pattern_macro_step_rows_from_graph_document,
    validate_graph_document,
)


def _rotate_doc() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_rot",
                "kind": "operation",
                "operation": OperationType.ROTATE_CW.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_rot", "kind": "input"},
            {"from": "o_rot", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }


def test_try_pattern_macro_step_rows_from_rotate_graph() -> None:
    rows = try_pattern_macro_step_rows_from_graph_document(_rotate_doc())
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["operation"] == OperationType.ROTATE_CW.value
    assert rows[0]["step_index"] == 1
    assert rows[0]["input_slots"] == ["CuCuCuCu"]
    assert rows[0]["output_slots"] == [""]
    assert rows[0]["note"] == "graph:o_rot"


def test_recompute_validated_matches_recompute_graph_document() -> None:
    raw = _rotate_doc()
    doc_full, w_full = recompute_graph_document(raw)
    validated = validate_graph_document(raw)
    doc_val, w_val = recompute_validated_graph_document(validated)
    assert w_full == w_val
    assert doc_full == doc_val


def test_validate_graph_document_ok() -> None:
    doc = validate_graph_document(_rotate_doc())
    assert doc["schema_version"] == 1
    assert len(doc["nodes"]) == 3


def test_default_empty_graph_document() -> None:
    doc = default_empty_graph_document()
    assert doc["schema_version"] == 1
    assert doc["nodes"] == []
    assert doc["edges"] == []


def test_recompute_delivery_copies_intermediate_to_target() -> None:
    base = _rotate_doc()
    base["nodes"].append(
        {
            "id": "tgt",
            "kind": "shape",
            "role": "target",
            "shape_code": "",
            "quantity": 1,
            "x": 600,
            "y": 0,
        },
    )
    base["edges"].append({"from": "s_out", "to": "tgt", "kind": "delivery"})
    doc, warnings = recompute_graph_document(base)
    assert not any("cycle" in w.lower() for w in warnings), warnings
    im = next(n for n in doc["nodes"] if n["id"] == "s_out")
    tgt = next(n for n in doc["nodes"] if n["id"] == "tgt")
    assert tgt["shape_code"] == im["shape_code"]
    assert tgt["shape_code"]


def test_recompute_rotate_updates_downstream_shape() -> None:
    doc, warnings = recompute_graph_document(_rotate_doc())
    assert not any("cycle" in w.lower() for w in warnings), warnings
    out_node = next(n for n in doc["nodes"] if n["id"] == "s_out")
    expected = apply_operation(OperationType.ROTATE_CW, ("CuCuCuCu",))[0]
    assert out_node["shape_code"] == expected


def test_recompute_cutter_updates_two_output_shapes() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_c",
                "kind": "operation",
                "operation": OperationType.CUTTER.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_l",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
            {
                "id": "s_r",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 40,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_c", "kind": "input"},
            {"from": "o_c", "to": "s_l", "kind": "output", "slot": "0"},
            {"from": "o_c", "to": "s_r", "kind": "output", "slot": "1"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    lnode = next(n for n in out["nodes"] if n["id"] == "s_l")
    rnode = next(n for n in out["nodes"] if n["id"] == "s_r")
    assert lnode["shape_code"] == "CuCu----"
    assert rnode["shape_code"] == "----CuCu"


def test_recompute_autocreate_second_cutter_output_uses_grid_not_stack() -> None:
    """세컨드 출력이 없을 때 자동 생성 노드는 2열 그리드(가로 오프셋)로 둔다."""
    ox, oy = 200.0, 50.0
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_cut",
                "kind": "operation",
                "operation": OperationType.CUTTER.value,
                "x": ox,
                "y": oy,
            },
            {
                "id": "s_first",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_cut", "kind": "input"},
            {"from": "o_cut", "to": "s_first", "kind": "output", "slot": "0"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert any("auto-created" in w for w in warnings)
    auto = next(
        n
        for n in out["nodes"]
        if n["kind"] == "shape" and n["id"] != "s_in" and n["id"] != "s_first"
    )
    expect_x = ox + RECIPE_GRAPH_AUTO_OUTPUT_X_OFFSET + float(RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING)
    expect_y = oy
    assert auto["x"] == expect_x
    assert auto["y"] == expect_y
    e2 = next(
        e
        for e in out["edges"]
        if e["from"] == "o_cut" and e["to"] == auto["id"] and e["kind"] == "output"
    )
    assert e2.get("slot") == "1"
    s_first = next(n for n in out["nodes"] if n["id"] == "s_first")
    # 첫 번째 슬롯(갱신)은 이전 x,y 유지, 두 번째는 열 1 → 가로로 분리
    assert abs(s_first["x"] - auto["x"]) >= float(RECIPE_GRAPH_AUTO_OUTPUT_COL_SPACING) * 0.9


def test_recompute_half_destroyer_updates_downstream_shape() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_hd",
                "kind": "operation",
                "operation": OperationType.HALF_DESTROYER.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_hd", "kind": "input"},
            {"from": "o_hd", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    out_node = next(n for n in out["nodes"] if n["id"] == "s_out")
    assert out_node["shape_code"] == "CuCu----"


def test_validate_painter_requires_paint_color() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
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
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_p", "kind": "input"},
            {"from": "o_p", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    try:
        validate_graph_document(doc)
    except ValueError as exc:
        assert "paint_color" in str(exc).lower()
    else:
        raise AssertionError("expected ValueError")


def test_recompute_painter_updates_shape() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
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
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_p", "kind": "input"},
            {"from": "o_p", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    node = next(n for n in out["nodes"] if n["id"] == "s_out")
    expected = apply_operation(OperationType.PAINTER, ("CuCu----",), paint_color="r")[0]
    assert node["shape_code"] == expected


def test_apply_operation_color_mixer_two_inputs() -> None:
    out = apply_operation(OperationType.COLOR_MIXER, ("CrCrCrCr", "CgCgCgCg"))
    assert out == ("CyCyCyCy",)


def test_recompute_color_mixer_updates_output_shape() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_r",
                "kind": "shape",
                "role": "source",
                "shape_code": "CrCrCrCr",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "s_g",
                "kind": "shape",
                "role": "source",
                "shape_code": "CgCgCgCg",
                "quantity": 1,
                "x": 0,
                "y": 80,
            },
            {
                "id": "o_mix",
                "kind": "operation",
                "operation": OperationType.COLOR_MIXER.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_r", "to": "o_mix", "kind": "input"},
            {"from": "s_g", "to": "o_mix", "kind": "input", "slot": "1"},
            {"from": "o_mix", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    node = next(n for n in out["nodes"] if n["id"] == "s_out")
    assert node["shape_code"] == "CyCyCyCy"


def test_apply_operation_splitter_two_identical_outputs() -> None:
    out = apply_operation(OperationType.SPLITTER, ("CuCu----",))
    assert out == ("CuCu----", "CuCu----")


def test_apply_operation_pin_pusher_prepends_pin_layer() -> None:
    out = apply_operation(OperationType.PIN_PUSHER, ("CuCuCuCu",))
    assert out == ("PuPuPuPu:CuCuCuCu",)


def test_recompute_splitter_fills_two_downstream_shapes() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_sp",
                "kind": "operation",
                "operation": OperationType.SPLITTER.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_a",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
            {
                "id": "s_b",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 80,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_sp", "kind": "input"},
            {"from": "o_sp", "to": "s_a", "kind": "output", "slot": "0"},
            {"from": "o_sp", "to": "s_b", "kind": "output", "slot": "1"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    a = next(n for n in out["nodes"] if n["id"] == "s_a")
    b = next(n for n in out["nodes"] if n["id"] == "s_b")
    assert a["shape_code"] == "CuCuCuCu"
    assert b["shape_code"] == "CuCuCuCu"


def test_recompute_pin_pusher_updates_downstream_shape() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_pp",
                "kind": "operation",
                "operation": OperationType.PIN_PUSHER.value,
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_pp", "kind": "input"},
            {"from": "o_pp", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    out, warnings = recompute_graph_document(doc)
    assert not warnings, warnings
    node = next(n for n in out["nodes"] if n["id"] == "s_out")
    assert node["shape_code"] == "PuPuPuPu:CuCuCuCu"


def test_apply_operation_painter_requires_paint_color_kwarg() -> None:
    with pytest.raises(ValueError, match="painter requires"):
        apply_operation(OperationType.PAINTER, ("CuCu----",))


def test_recompute_rejects_cycle() -> None:
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s0",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 100, "y": 0},
            {
                "id": "i1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
            {"id": "o2", "kind": "operation", "operation": "rotate_cw", "x": 300, "y": 0},
            {
                "id": "i2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
            {"id": "o3", "kind": "operation", "operation": "rotate_cw", "x": 500, "y": 0},
            {
                "id": "i3",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 600,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s0", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "i1", "kind": "output", "slot": "0"},
            {"from": "i1", "to": "o2", "kind": "input"},
            {"from": "o2", "to": "i2", "kind": "output", "slot": "0"},
            {"from": "i2", "to": "o3", "kind": "input"},
            {"from": "o3", "to": "i3", "kind": "output", "slot": "0"},
            {"from": "i3", "to": "o1", "kind": "input"},
        ],
    }
    _, warnings = recompute_graph_document(doc)
    assert any("cycle" in w.lower() for w in warnings)
