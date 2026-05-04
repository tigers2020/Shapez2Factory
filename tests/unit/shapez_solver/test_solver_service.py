import pytest

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.recipe import SolveContext
from django_apps.shapez_solver.dto.solver_graph import SolverOperationNode, SolverShapeNode
from django_apps.shapez_solver.services.factory_throughput_service import (
    FactoryThroughputRequest,
    FactoryThroughputResult,
    FactoryThroughputService,
)
from django_apps.shapez_solver.services.planner_service import (
    PlannerService,
    UnsupportedTargetError,
)


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def _throughput(code: str) -> FactoryThroughputResult:
    return FactoryThroughputService().solve(FactoryThroughputRequest(target_shape=_shape(code)))


def _shape_nodes(nodes: tuple[object, ...]) -> list[SolverShapeNode]:
    return [node for node in nodes if isinstance(node, SolverShapeNode)]


def _operation_nodes(nodes: tuple[object, ...]) -> list[SolverOperationNode]:
    return [node for node in nodes if isinstance(node, SolverOperationNode)]


def test_inventory_throughput_full_source_is_no_op() -> None:
    result = _throughput("CuCuCuCu")
    assert result.found is True
    assert result.graph is not None
    assert result.steps == ()
    shape_nodes = _shape_nodes(result.graph.nodes)
    assert len(shape_nodes) == 1
    assert shape_nodes[0].role == "target"


def test_inventory_throughput_rc_cu_rc_cu_short_plan() -> None:
    result = _throughput("RcCuRcCu")
    assert result.found is True
    assert result.batch_plan is not None
    assert len(result.steps) < 12
    assert "CHECKER_PAIR" in result.batch_plan.used_macro_kinds


def test_inventory_throughput_swap_half_pattern() -> None:
    result = _throughput("RcRcCuCu")
    assert result.found is True
    op_types = [step.operation_type for step in result.steps]
    assert "swapper" in op_types
    assert all(t in ("swapper", "rotate_cw", "rotate_ccw", "rotate_180") for t in op_types)


def test_inventory_cannot_paint_monochrome_target_yet() -> None:
    result = _throughput("CrCrCrCr")
    assert result.found is False


def test_inventory_multi_layer_target_no_batch() -> None:
    result = _throughput("CuCuCuCu:RuRuRuRu")
    assert result.found is False
    assert result.warnings


def test_inventory_cu_ru_su_su_batch_demands_and_optional_plan() -> None:
    result = _throughput("CuRuSuSu")
    assert result.target_count == 4
    assert tuple(d.base_shape_code for d in result.base_demands) == (
        "CuCuCuCu",
        "RuRuRuRu",
        "SuSuSuSu",
    )
    assert result.found is True
    assert result.batch_plan is not None
    assert "ABCC_BATCH" in result.batch_plan.used_macro_kinds
    assert result.graph is not None
    sources = {
        node.shape_code: node.quantity
        for node in _shape_nodes(result.graph.nodes)
        if node.role == "source"
    }
    assert sources == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
    targets = [n for n in _shape_nodes(result.graph.nodes) if n.role == "target"]
    assert len(targets) == 1
    assert targets[0].quantity == 4


def test_planner_memoizes_repeated_shape_requests() -> None:
    planner = PlannerService()
    ctx = SolveContext()
    target = _shape("CuCu----")

    first = planner.solve_shape(target, ctx)
    second = planner.solve_shape(target, ctx)

    assert first is second
    assert target.canonical_code in ctx.memo


def test_throughput_rejects_unsupported_pin_and_crystal_targets() -> None:
    with pytest.raises(UnsupportedTargetError):
        _throughput("PuPuPuPu")

    with pytest.raises(UnsupportedTargetError):
        _throughput("cu----cu")
