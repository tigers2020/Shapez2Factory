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


def _shape_nodes(nodes: tuple[SolverShapeNode | SolverOperationNode, ...]) -> list[SolverShapeNode]:
    return [node for node in nodes if isinstance(node, SolverShapeNode)]


def _operation_nodes(
    nodes: tuple[SolverShapeNode | SolverOperationNode, ...],
) -> list[SolverOperationNode]:
    return [node for node in nodes if isinstance(node, SolverOperationNode)]


def test_solver_builds_source_shape_graph() -> None:
    result = _throughput("CuCuCuCu")

    assert result.target_shape == "CuCuCuCu"
    assert result.graph is not None
    shape_nodes = _shape_nodes(result.graph.nodes)
    assert len(shape_nodes) == 1
    assert shape_nodes[0].role == "target"


def test_solver_uses_rotation_rule_for_rotated_half() -> None:
    result = _throughput("--CuCu--")

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    operation_types = {node.operation_type for node in operation_nodes}
    assert "cutter" in operation_types
    assert "rotate_cw" in operation_types or "rotate_ccw" in operation_types


def test_solver_uses_painter_for_monochrome_colored_shape() -> None:
    result = _throughput("CrCrCrCr")

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    assert any(node.operation_type == "painter" for node in operation_nodes)


def test_solver_builds_quadrant_assembly_graph_for_mixed_single_layer_shape() -> None:
    result = _throughput("CuRuSuWu")

    assert result.graph is not None
    target_nodes = [node for node in _shape_nodes(result.graph.nodes) if node.role == "target"]
    assert len(target_nodes) == 1
    assert target_nodes[0].shape_code == "CuRuSuWu"
    assert any(edge.label == "Output B (unused)" for edge in result.graph.edges)
    operation_nodes = _operation_nodes(result.graph.nodes)
    operation_types = [node.operation_type for node in operation_nodes]
    assert operation_types.count("stacker") == 2
    assert operation_types.count("swapper") == 1


def test_solver_prefers_structured_half_assembly_for_mixed_single_layer_shapes() -> None:
    result = _throughput("CuRuSuSu")

    assert result.graph is not None
    operation_types = [node.operation_type for node in _operation_nodes(result.graph.nodes)]
    assert operation_types.count("stacker") == 1
    assert operation_types.count("swapper") == 1


def test_solver_builds_multi_layer_stack_graph() -> None:
    result = _throughput("CuCuCuCu:RuRuRuRu")

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    assert any(node.operation_type == "stacker" for node in operation_nodes)


def test_solver_service_applies_auto_lcm_batch_to_graph_sources() -> None:
    result = _throughput("CuRuSuSu")
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


def test_solver_rejects_unsupported_pin_and_crystal_targets() -> None:
    with pytest.raises(UnsupportedTargetError):
        _throughput("PuPuPuPu")

    with pytest.raises(UnsupportedTargetError):
        _throughput("cu----cu")
