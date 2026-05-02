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


def test_cutter_returns_stable_left_and_right_outputs() -> None:
    engine = OperationEngine()
    left, right = engine.cut(_shape("CuCuCuCu"))

    assert left.canonical_code == "CuCu----"
    assert right.canonical_code == "----CuCu"


def test_swapper_combines_left_and_right_halves() -> None:
    engine = OperationEngine()
    output_a, output_b = engine.swapper(_shape("CuCu----"), _shape("----RuRu"))

    assert output_a.canonical_code == "CuCuRuRu"
    assert output_b.canonical_code == "--------"


def test_stacker_merges_disjoint_quadrants_before_creating_new_layer() -> None:
    engine = OperationEngine()
    result = engine.stacker(_shape("Cu------"), _shape("----Ru--"))

    assert result.canonical_code == "Cu--Ru--"


def test_painter_recolors_non_empty_parts() -> None:
    engine = OperationEngine()
    (result,) = engine.apply(OperationType.PAINTER, (_shape("CuCu----"),), color="r")

    assert result.canonical_code == "CrCr----"
