from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    SolveContext,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.services.operation_engine import OperationEngine
from django_apps.shapez_solver.services.planner_service import PlannerService
from django_apps.shapez_solver.services.planner_support import (
    build_binary_operation_solution_overlapping_deps,
    build_operation_solution,
)
from django_apps.shapez_solver.services.prebuilt_pattern_registry import match_prebuilt_pattern


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def _solve(code: str) -> SolvedRecipe:
    return PlannerService().solve_shape(_shape(code), SolveContext())


def _operation_types(code: str) -> list[str]:
    solved = _solve(code)
    return [
        recipe.operation_type.value
        for recipe in solved.recipes
        if isinstance(recipe, OperationRecipe)
    ]


def _source_codes(code: str) -> list[str]:
    solved = _solve(code)
    return [
        recipe.shape.canonical_code for recipe in solved.recipes if isinstance(recipe, SourceRecipe)
    ]


def test_half_and_half_pattern_uses_prebuilt_swapper_recipe() -> None:
    assert _operation_types("CuCuRuRu") == ["cutter", "cutter", "swapper"]


def test_half_and_half_pattern_resolves_half_swapper_template() -> None:
    match = match_prebuilt_pattern(_shape("CuCuRuRu"), operation_engine=OperationEngine())

    assert match is not None
    assert match.definition.family_id == "half_and_half"
    assert match.template.template_id == "half_swapper"
    assert match.template.input_ports == ("leftSource", "rightSource")
    assert match.template.output_ports == ("targetShape",)


def test_half_and_half_rotated_variant_uses_prebuilt_rotation_finish() -> None:
    assert _operation_types("CuRuRuCu") == ["cutter", "cutter", "swapper", "rotate_ccw"]


def test_half_and_half_colored_variant_keeps_color_aware_recipe() -> None:
    assert _operation_types("CrCrRgRg") == [
        "painter",
        "cutter",
        "painter",
        "cutter",
        "swapper",
    ]


def test_checker_pattern_uses_prebuilt_registry_without_duplicate_sources() -> None:
    operation_types = _operation_types("CuRuCuRu")

    assert operation_types.count("swapper") == 1
    assert operation_types.count("rotate_180") == 1
    assert len(operation_types) == 9
    assert _source_codes("CuRuCuRu") == ["CuCuCuCu", "RuRuRuRu"]


def test_checker_pattern_resolves_checker_swapper_template() -> None:
    match = match_prebuilt_pattern(_shape("CuRuCuRu"), operation_engine=OperationEngine())

    assert match is not None
    assert match.definition.family_id == "checker"
    assert match.template.template_id == "checker_swapper"
    assert match.template.input_ports == ("leftHalf",)
    assert match.template.output_ports == ("targetShape",)


def test_checker_colored_variant_uses_prebuilt_registry() -> None:
    operation_types = _operation_types("CrRgCrRg")

    assert operation_types.count("swapper") == 1
    assert operation_types.count("rotate_180") == 1
    assert _source_codes("CrRgCrRg") == ["CuCuCuCu", "RuRuRuRu"]


def test_unregistered_pattern_falls_back_to_generic_rules() -> None:
    assert len(_operation_types("CuRuSuWu")) == 15
    assert _source_codes("CuRuSuWu") == ["CuCuCuCu", "RuRuRuRu", "SuSuSuSu", "WuWuWuWu"]


def test_unregistered_half_target_uses_single_half_stack() -> None:
    operation_types = _operation_types("CuRu----")

    assert operation_types.count("stacker") == 1
    assert operation_types.count("swapper") == 0


def test_disjoint_binary_prebuilt_matches_build_operation_solution_cost() -> None:
    """의존 그래프가 겹치지 않을 때는 overlapping 빌더 비용이 build_operation_solution 과 같다."""
    ctx = SolveContext()
    engine = OperationEngine()
    left = PlannerService().solve_shape(_shape("CuCuCuCu"), ctx)
    right = PlannerService().solve_shape(_shape("RuRuRuRu"), ctx)
    outputs = engine.apply(OperationType.SWAPPER, (left.ref.shape, right.ref.shape))
    expected = build_operation_solution(
        SolveContext(),
        operation_type=OperationType.SWAPPER,
        inputs=(left.ref, right.ref),
        outputs=outputs,
        selected_output_index=0,
        label="Swapper",
        description="Swapper",
        dependencies=(left, right),
    )
    got = build_binary_operation_solution_overlapping_deps(
        SolveContext(),
        operation_type=OperationType.SWAPPER,
        left=left,
        right=right,
        outputs=outputs,
        selected_output_index=0,
        label="Swapper",
        description="Swapper",
    )
    assert got.cost == expected.cost
