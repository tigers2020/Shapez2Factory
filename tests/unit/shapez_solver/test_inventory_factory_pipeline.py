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


def test_inventory_throughput_finds_short_checker_plan_for_rc_cu_rc_cu() -> None:
    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("RcCuRcCu"),
            solver_timeout_seconds=30.0,
        )
    )

    assert result.solver_mode == "inventory_search"
    assert result.batch_plan is not None
    assert result.solved_recipe is None
    assert result.materialized_graph is None
    assert result.graph is not None
    assert len(result.steps) < 10
    assert "CHECKER_PAIR" in result.batch_plan.used_macro_kinds

    target_nodes = [
        n for n in result.graph.nodes if isinstance(n, SolverShapeNode) and n.role == "target"
    ]
    assert len(target_nodes) == 1
    assert target_nodes[0].shape_code == "RcCuRcCu"
    assert target_nodes[0].quantity == result.target_count


def test_inventory_throughput_multi_layer_not_found() -> None:
    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("CuCuCuCu:RuRuRuRu"),
        )
    )
    assert result.found is False
    assert result.graph is None
