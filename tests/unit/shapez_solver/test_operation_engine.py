import pytest

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_engine import OperationEngine


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_rotate_operations_produce_expected_codes() -> None:
    engine = OperationEngine()
    shape = _shape("RuSuCuWu")

    assert engine.rotate_cw(shape).canonical_code == "WuRuSuCu"
    assert engine.rotate_ccw(shape).canonical_code == "SuCuWuRu"
    assert engine.rotate_180(shape).canonical_code == "CuWuRuSu"


def test_cutter_returns_west_then_east_halves() -> None:
    """Cut returns (west_half, east_half); see shape_encoding and shapez2_cutter_outputs."""

    engine = OperationEngine()
    west, east = engine.cut(_shape("CuCuCuCu"))

    assert west.canonical_code == "CuCu----"
    assert east.canonical_code == "----CuCu"


def test_cutter_splits_each_layer_independently() -> None:
    engine = OperationEngine()
    west, east = engine.cut(_shape("CuCuCuCu:RuRuRuRu"))

    assert west.canonical_code == "CuCu----:RuRu----"
    assert east.canonical_code == "----CuCu:----RuRu"


def test_half_destroyer_keeps_west_half() -> None:
    engine = OperationEngine()
    (only,) = engine.apply(OperationType.HALF_DESTROYER, (_shape("CuCuCuCu"),))
    west, _east = engine.cut(_shape("CuCuCuCu"))

    assert only.canonical_code == west.canonical_code


def test_half_destroyer_keeps_west_half_on_each_layer() -> None:
    engine = OperationEngine()
    (only,) = engine.apply(OperationType.HALF_DESTROYER, (_shape("CuCuCuCu:RuRuRuRu"),))
    west, _east = engine.cut(_shape("CuCuCuCu:RuRuRuRu"))

    assert only.canonical_code == west.canonical_code


def test_swapper_combines_left_and_right_halves() -> None:
    engine = OperationEngine()
    output_a, output_b = engine.swapper(_shape("CuCu----"), _shape("----RuRu"))

    assert output_a.canonical_code == "CuCuRuRu"
    assert output_b.canonical_code == "--------"


def test_swapper_swaps_each_layer_when_layer_counts_match() -> None:
    engine = OperationEngine()
    left = _shape("CuCu----:RuRu----")
    right = _shape("----SgSg:----SbSb")
    output_a, output_b = engine.swapper(left, right)

    assert output_a.canonical_code == "CuCuSgSg:RuRuSbSb"
    assert output_b.canonical_code == "--------:--------"


def test_swapper_pads_shorter_shape_with_empty_top_layers() -> None:
    engine = OperationEngine()
    output_a, output_b = engine.swapper(_shape("CuCu----"), _shape("CuCu----:RuRu----"))

    assert output_a.canonical_code == "CuCu----:--------"
    assert output_b.canonical_code == "CuCu----:RuRu----"


def test_swapper_preserves_multi_layer_when_other_input_is_single_layer() -> None:
    """Regression: misaligned depth must not degenerate to single-layer swap semantics."""

    engine = OperationEngine()
    output_a, output_b = engine.swapper(
        _shape("WrCrRgSy:RcRcRrRr"),
        _shape("RuRuRuRu"),
    )

    assert output_a.canonical_code == "WrCrRuRu:RcRc----"
    assert output_b.canonical_code == "RuRuRgSy:----RrRr"


def test_stacker_concat_when_first_layers_do_not_merge_disjoint() -> None:
    engine = OperationEngine()
    bottom = _shape("CuWu----:CuRc----")
    top = _shape("CuWuSuRu")
    result = engine.stacker(bottom, top)

    # merge_disjoint fails on first layers; concat then column gravity settles quadrants.
    assert result.canonical_code == "CuWuSuRu:CuRc----:CuWu----"


def test_stacker_merges_bottom_and_top_first_layers_when_disjoint() -> None:
    engine = OperationEngine()
    bottom = _shape("----SuRu:----SuWb")
    top = _shape("SuRu----")
    result = engine.stacker(bottom, top)

    assert result.canonical_code == "SuRuSuRu:----SuWb"


def test_stacker_merges_disjoint_quadrants_before_creating_new_layer() -> None:
    engine = OperationEngine()
    result = engine.stacker(_shape("Cu------"), _shape("----Ru--"))

    assert result.canonical_code == "Cu--Ru--"


def test_painter_recolors_non_empty_parts() -> None:
    engine = OperationEngine()
    (result,) = engine.apply(OperationType.PAINTER, (_shape("CuCu----"),), color="r")

    assert result.canonical_code == "CrCr----"


def test_painter_does_not_recolor_pins() -> None:
    engine = OperationEngine()
    (result,) = engine.apply(OperationType.PAINTER, (_shape("P-P-P-P-:CuCuCuCu"),), color="r")

    assert result.canonical_code == "P-P-P-P-:CrCrCrCr"


def test_painter_applies_pure_fluid_color_with_two_inputs() -> None:
    engine = OperationEngine()
    target = _shape("CuCu----")
    fluid = _shape("CrCrCrCr")
    (result,) = engine.apply(OperationType.PAINTER, (target, fluid))

    assert result.canonical_code == "CrCr----"


def test_stacker_column_gravity_moves_pin_down_through_empty_quadrant() -> None:
    engine = OperationEngine()
    bottom = _shape("--CuCuCu")
    top = _shape("P-CuCuCu")
    result = engine.stacker(bottom, top)

    assert result.canonical_code == "P-CuCuCu:--CuCuCu"


def test_stacker_enforces_max_layers_dropping_top_layers() -> None:
    engine = OperationEngine()
    bottom = _shape("CuCuCuCu:RuRuRuRu:SuSuSuSu:WuWuWuWu")
    top = _shape("CgCgCgCg:CrCrCrCr")
    result = engine.stacker(bottom, top)

    assert result.canonical_code == "CuCuCuCu:RuRuRuRu:SuSuSuSu:WuWuWuWu"


def test_pin_pusher_drops_top_layer_when_exceeding_max_layers() -> None:
    engine = OperationEngine()
    four = _shape("CuCuCuCu:RuRuRuRu:SuSuSuSu:WuWuWuWu")
    (result,) = engine.apply(OperationType.PIN_PUSHER, (four,))

    assert result.canonical_code == "P-P-P-P-:CuCuCuCu:RuRuRuRu:SuSuSuSu"


def test_color_mixer_merges_primary_rgb_on_matching_geometry() -> None:
    engine = OperationEngine()
    result = engine.color_mixer(_shape("CrCrCrCr"), _shape("CgCgCgCg"))

    assert result.canonical_code == "CyCyCyCy"


def test_merge_accepts_identical_canonical_shapes() -> None:
    engine = OperationEngine()
    a = _shape("CuCuCuCu")
    b = _shape("CuCuCuCu")
    (out,) = engine.apply(OperationType.MERGE, (a, b))
    assert out.canonical_code == "CuCuCuCu"


def test_merge_rejects_different_shapes() -> None:
    engine = OperationEngine()
    with pytest.raises(ValueError, match="identical canonical"):
        engine.apply(OperationType.MERGE, (_shape("CuCuCuCu"), _shape("RuRuRuRu")))


def test_color_mixer_preserves_shape_when_one_side_uncolored() -> None:
    engine = OperationEngine()
    result = engine.color_mixer(_shape("CuCuCuCu"), _shape("CrCrCrCr"))

    assert result.canonical_code == "CrCrCrCr"


def test_splitter_duplicates_input_on_two_outputs() -> None:
    engine = OperationEngine()
    a, b = engine.splitter(_shape("CuCu----"))

    assert a.canonical_code == b.canonical_code == "CuCu----"


def test_pin_pusher_adds_bottom_pin_layer() -> None:
    engine = OperationEngine()
    (out,) = engine.apply(OperationType.PIN_PUSHER, (_shape("CuCuCuCu"),))

    assert out.canonical_code == "P-P-P-P-:CuCuCuCu"


def test_crystal_generator_fills_gaps_and_pins() -> None:
    engine = OperationEngine()
    # SW=Ru, NW=--, NE=Ru, SE=-- ??gaps NW/SE ??RuccRucc
    base = _shape("Ru--Ru--")
    (out,) = engine.apply(OperationType.CRYSTAL_GENERATOR, (base, base), color="c")

    assert out.canonical_code == "RuccRucc"


def test_crystal_generator_requires_color() -> None:
    engine = OperationEngine()
    with pytest.raises(ValueError, match="crystal_generator requires an explicit color"):
        engine.apply(OperationType.CRYSTAL_GENERATOR, (_shape("CuCuCuCu"), _shape("CuCuCuCu")))
