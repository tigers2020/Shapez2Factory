from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.recipe import OperationRecipe, SolveContext
from django_apps.shapez_solver.services.planner_service import PlannerService


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_legacy_planner_rc_cu_rc_cu_uses_multiple_cutters() -> None:
    """레거시 플래너가 체커형 타깃에서 cutter를 여러 번 쓰는지 고정한다."""

    solved = PlannerService().solve_shape(_shape("RcCuRcCu"), SolveContext())
    op_types = [
        recipe.operation_type.value
        for recipe in solved.recipes
        if isinstance(recipe, OperationRecipe)
    ]
    assert op_types.count("cutter") >= 4
