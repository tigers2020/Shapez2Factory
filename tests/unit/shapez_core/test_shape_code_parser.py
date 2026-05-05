from __future__ import annotations

import pytest

from django_apps.shapez_core.domain.shape_pattern import QuadrantPosition
from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_codec import (
    normalize_shape,
    pattern_from_shape,
    shape_from_pattern,
)
from django_apps.shapez_solver.dto.solver_graph import SolverShapeNode
from django_apps.shapez_solver.services.factory_throughput_service import (
    FactoryThroughputRequest,
    FactoryThroughputService,
)
from django_apps.shapez_solver.services.planner_service import (
    PlannerRequest,
    PlannerService,
)


def test_parse_single_pattern_without_brackets() -> None:
    parsed = parse_shape_code_list("SuSuSuSu")
    assert len(parsed) == 1
    pattern = parsed[0]
    assert pattern.normalized_code == "SuSuSuSu"
    assert len(pattern.layers) == 1
    assert [cell.position for cell in pattern.layers[0].cells] == [
        QuadrantPosition.SW,
        QuadrantPosition.NW,
        QuadrantPosition.NE,
        QuadrantPosition.SE,
    ]


def test_parse_cr_ru_quadrants_sw_nw() -> None:
    parsed = parse_shape_code_list("CrRu----")
    cells = parsed[0].layers[0].cells
    assert cells[0].raw_token == "Cr" and cells[0].position == QuadrantPosition.SW
    assert cells[1].raw_token == "Ru" and cells[1].position == QuadrantPosition.NW


def test_parse_ru_su_cu_wu_quadrants() -> None:
    parsed = parse_shape_code_list("RuSuCuWu")
    cells = parsed[0].layers[0].cells
    assert cells[0].raw_token == "Ru" and cells[0].position == QuadrantPosition.SW
    assert cells[1].raw_token == "Su" and cells[1].position == QuadrantPosition.NW
    assert cells[2].raw_token == "Cu" and cells[2].position == QuadrantPosition.NE
    assert cells[3].raw_token == "Wu" and cells[3].position == QuadrantPosition.SE


def test_parse_single_pattern_with_brackets() -> None:
    parsed = parse_shape_code_list("[SuSuSuSu]")
    assert len(parsed) == 1
    assert parsed[0].normalized_code == "SuSuSuSu"


def test_parse_comma_separated_patterns() -> None:
    parsed = parse_shape_code_list("[RuRuRuRu, WrCrRgSy]")
    assert len(parsed) == 2
    assert parsed[0].normalized_code == "RuRuRuRu"
    assert parsed[1].normalized_code == "WrCrRgSy"


def test_parse_stacked_layers() -> None:
    parsed = parse_shape_code_list("RuRuRuRu:WrCrRgSy")
    assert len(parsed) == 1
    pattern = parsed[0]
    assert pattern.normalized_code == "RuRuRuRu:WrCrRgSy"
    assert len(pattern.layers) == 2
    assert pattern.layers[0].layer_index == 0
    assert pattern.layers[1].layer_index == 1


def test_parse_empty_quadrant_token() -> None:
    parsed = parse_shape_code_list("--RuRuRu")
    assert len(parsed) == 1
    cell0 = parsed[0].layers[0].cells[0]
    assert cell0.shape_code == "-"
    assert cell0.color_code == "-"
    assert cell0.shape_kind == "empty"
    assert cell0.color_kind == "empty"


def test_unknown_shape_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="unknown shape"):
        parse_shape_code_list("XuXuXuXu")


def test_unknown_color_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="unknown color"):
        parse_shape_code_list("SzSzSzSz")


def test_wrong_layer_length_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="must be 8 characters"):
        parse_shape_code_list("SuSuSu")


def test_non_colorable_shape_rejected_with_color() -> None:
    with pytest.raises(ShapeCodeParseError, match="pin quadrant must be P-"):
        parse_shape_code_list("PrPrPrPr")


def test_pin_pu_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="pin quadrant must be P-"):
        parse_shape_code_list("PuPuPuPu")


def test_pin_ok() -> None:
    parsed = parse_shape_code_list("P-P-P-P-")
    cell0 = parsed[0].layers[0].cells[0]
    assert cell0.shape_kind == "pin"
    assert cell0.raw_token == "P-"
    assert cell0.color_code == "-"
    assert cell0.color_kind == "uncolored"


def test_emptiness_mismatch_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="emptiness mismatch"):
        parse_shape_code_list("S-S-S-S-")


def test_empty_input_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="empty"):
        parse_shape_code_list("   ")


def test_mismatched_brackets_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="mismatched"):
        parse_shape_code_list("[SuSuSuSu")


def test_unexpected_bracket_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="unexpected bracket"):
        parse_shape_code_list("Su]SuSuSu")


def test_empty_segment_rejected() -> None:
    with pytest.raises(ShapeCodeParseError, match="empty pattern segment"):
        parse_shape_code_list("[SuSuSuSu,]")


def test_pin_round_trips_through_pattern_codec() -> None:
    pattern = parse_shape_code_list("P-P-P-P-:CuCuCuCu")[0]
    shape = shape_from_pattern(pattern)
    assert shape.canonical_code == "P-P-P-P-:CuCuCuCu"
    assert pattern_from_shape(shape).normalized_code == "P-P-P-P-:CuCuCuCu"


def test_shape_value_object_round_trips_through_pattern_codec() -> None:
    pattern = parse_shape_code_list("RuRuRuRu:WrCrRgSy")[0]
    shape = shape_from_pattern(pattern)

    assert shape.canonical_code == "RuRuRuRu:WrCrRgSy"
    rebuilt_pattern = pattern_from_shape(shape)
    assert rebuilt_pattern.normalized_code == "RuRuRuRu:WrCrRgSy"
    assert normalize_shape(shape).canonical_code == "RuRuRuRu:WrCrRgSy"


def test_solver_and_planner_use_target_shape() -> None:
    target = parse_shape_code_list("CuCuCuCu")[0]
    shape = shape_from_pattern(target)
    solver_result = FactoryThroughputService().solve(FactoryThroughputRequest(target_shape=shape))

    assert solver_result.target_shape == "CuCuCuCu"
    assert solver_result.graph is not None
    target_nodes = [
        node
        for node in solver_result.graph.nodes
        if isinstance(node, SolverShapeNode) and node.role == "target"
    ]
    assert len(target_nodes) == 1
    assert PlannerService().plan(
        PlannerRequest(target_shape=shape, target_rate_per_min=60.0)
    ).required_inputs == ("CuCuCuCu",)
