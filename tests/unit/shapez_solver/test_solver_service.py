import pytest

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.recipe import SolveContext
from django_apps.shapez_solver.dto.solver_graph import SolverOperationNode, SolverShapeNode
from django_apps.shapez_solver.services.planner_service import (
    PlannerService,
    UnsupportedTargetError,
)
from django_apps.shapez_solver.services.solver_service import SolverRequest, SolverService


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def _shape_nodes(nodes: tuple[SolverShapeNode | SolverOperationNode, ...]) -> list[SolverShapeNode]:
    return [node for node in nodes if isinstance(node, SolverShapeNode)]


def _operation_nodes(
    nodes: tuple[SolverShapeNode | SolverOperationNode, ...],
) -> list[SolverOperationNode]:
    return [node for node in nodes if isinstance(node, SolverOperationNode)]


def test_solver_builds_source_shape_graph() -> None:
    result = SolverService().solve(SolverRequest(target_shape=_shape("CuCuCuCu")))

    assert result.target_shape == "CuCuCuCu"
    assert result.graph is not None
    shape_nodes = _shape_nodes(result.graph.nodes)
    assert len(shape_nodes) == 1
    assert shape_nodes[0].role == "target"


def test_solver_uses_rotation_rule_for_rotated_half() -> None:
    result = SolverService().solve(SolverRequest(target_shape=_shape("--CuCu--")))

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    operation_types = {node.operation_type for node in operation_nodes}
    assert "cutter" in operation_types
    assert "rotate_cw" in operation_types or "rotate_ccw" in operation_types


def test_solver_uses_painter_for_monochrome_colored_shape() -> None:
    result = SolverService().solve(SolverRequest(target_shape=_shape("CrCrCrCr")))

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    assert any(node.operation_type == "painter" for node in operation_nodes)


def test_solver_builds_quadrant_assembly_graph_for_mixed_single_layer_shape() -> None:
    result = SolverService().solve(SolverRequest(target_shape=_shape("CuRuSuWu")))

    assert result.graph is not None
    target_nodes = [node for node in _shape_nodes(result.graph.nodes) if node.role == "target"]
    assert len(target_nodes) == 1
    assert target_nodes[0].shape_code == "CuRuSuWu"
    assert any(edge.label == "Output B (unused)" for edge in result.graph.edges)


def test_solver_builds_multi_layer_stack_graph() -> None:
    result = SolverService().solve(SolverRequest(target_shape=_shape("CuCuCuCu:RuRuRuRu")))

    assert result.graph is not None
    operation_nodes = _operation_nodes(result.graph.nodes)
    assert any(node.operation_type == "stacker" for node in operation_nodes)


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
        SolverService().solve(SolverRequest(target_shape=_shape("PuPuPuPu")))

    with pytest.raises(UnsupportedTargetError):
        SolverService().solve(SolverRequest(target_shape=_shape("cu----cu")))
