from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.recipe import OperationRecipe, SolveContext
from django_apps.shapez_solver.services.planner_service import PlannerService


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_planner_solves_colored_shape_via_painter_rule() -> None:
    solved = PlannerService().solve_shape(_shape("CrCrCrCr"), SolveContext())

    assert solved.ref.shape.canonical_code == "CrCrCrCr"
    assert any(
        isinstance(recipe, OperationRecipe) and recipe.operation_type.value == "painter"
        for recipe in solved.recipes
    )


def test_planner_memoizes_repeated_target_in_context() -> None:
    planner = PlannerService()
    ctx = SolveContext()
    target = _shape("CuCu----")

    first = planner.solve_shape(target, ctx)
    second = planner.solve_shape(target, ctx)

    assert first is second
    assert ctx.memo[target.canonical_code] is first


def test_planner_balances_multi_layer_stacking_depth() -> None:
    solved = PlannerService().solve_shape(
        _shape("CuCuCuCu:RuRuRuRu:SuSuSuSu:WuWuWuWu"),
        SolveContext(),
    )

    assert solved.cost.operations == 3
    assert solved.cost.depth == 3
