import pytest

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.dto.solver_graph import SolverShapeNode
from django_apps.shapez_solver.models import MacroRecipe, PatternFamily
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
        )
    )

    assert result.target_count == 4
    assert tuple(demand.base_shape_code for demand in result.base_demands) == (
        "CuCuCuCu",
        "RuRuRuRu",
        "SuSuSuSu",
    )
    assert result.materialized_graph is None
    assert result.found is True
    assert result.graph is not None
    assert result.batch_plan is not None
    assert "ABCC_BATCH" in result.batch_plan.used_macro_kinds
    target_nodes = [
        node
        for node in result.graph.nodes
        if isinstance(node, SolverShapeNode) and node.role == "target"
    ]
    assert len(target_nodes) == 1
    assert target_nodes[0].quantity == 4
    source_nodes = [
        node
        for node in result.graph.nodes
        if isinstance(node, SolverShapeNode) and node.role == "source"
    ]
    by_code = {node.shape_code: node.quantity for node in source_nodes}
    assert by_code == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}


def test_factory_throughput_service_multi_layer_returns_not_found() -> None:
    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("CuCuCuCu:RuRuRuRu"),
        )
    )

    assert result.found is False
    assert result.base_demands == ()
    assert result.graph is None
    assert result.materialized_graph is None
    assert result.warnings


@pytest.mark.django_db
def test_factory_throughput_service_uses_db_catalog_macro_when_available() -> None:
    family = PatternFamily.objects.create(
        code="abcc",
        name="ABCC",
        signature="ABCC",
    )
    MacroRecipe.objects.create(
        family=family,
        code="abcc-batch",
        strategy_code="ABCC_BATCH",
        name="ABCC Batch",
    )

    result = FactoryThroughputService().solve(
        FactoryThroughputRequest(
            target_shape=_shape("CuRuSuSu"),
        )
    )

    assert result.batch_plan is not None
    assert result.batch_plan.used_macro_kinds == ("ABCC_BATCH",)
    assert result.batch_plan.used_macro_sources == ("ABCC_BATCH:db",)
