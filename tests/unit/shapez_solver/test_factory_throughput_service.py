from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.dto.solver_graph import SolverShapeNode
from django_apps.shapez_solver.services.factory_throughput_service import (
    FactoryThroughputRequest,
    FactoryThroughputService,
)


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_factory_throughput_service_attaches_base_demands_and_target_quantity() -> None:
    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("CuRuSuSu"),
            target_count=4,
        )
    )

    assert result.target_count == 4
    assert tuple(demand.base_shape_code for demand in result.base_demands) == (
        "CuCuCuCu",
        "RuRuRuRu",
        "SuSuSuSu",
    )
    assert result.graph is not None
    target_nodes = [
        node
        for node in result.graph.nodes
        if isinstance(node, SolverShapeNode) and node.role == "target"
    ]
    assert len(target_nodes) == 1
    assert target_nodes[0].quantity == 4


def test_factory_throughput_service_keeps_solving_when_base_demands_are_unsupported() -> None:
    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("CuCuCuCu:RuRuRuRu"),
            target_count=3,
        )
    )

    assert result.target_count == 3
    assert result.base_demands == ()
    assert result.graph is not None
    assert result.warnings
