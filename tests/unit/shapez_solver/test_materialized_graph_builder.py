from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.factory_demand import compute_factory_batch
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverOperationNode,
    SolverShapeNode,
)
from django_apps.shapez_solver.services.solve_pipeline import solve_recipe_pipeline


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def _materialized_graph(code: str) -> SolverGraph:
    shape = _shape(code)
    batch = compute_factory_batch(shape)
    result = solve_recipe_pipeline(
        shape,
        target_count=batch.target_count,
        base_demands=batch.base_demands,
    )
    assert result.materialized_graph is not None
    return result.materialized_graph


def test_materialized_graph_builder_uses_half_batch_path_for_direct_half_targets() -> None:
    graph = _materialized_graph("RuRu----")

    shape_nodes = [node for node in graph.nodes if isinstance(node, SolverShapeNode)]
    operation_nodes = [node for node in graph.nodes if isinstance(node, SolverOperationNode)]
    operation_types = [node.operation_type for node in operation_nodes]

    sources = [node for node in shape_nodes if node.role == "source"]
    targets = [node for node in shape_nodes if node.role == "target"]

    assert len(sources) == 1
    assert len(targets) == 2
    assert operation_types == ["cutter", "rotate_180"]
    assert "stacker" not in operation_types


def test_materialized_graph_builder_uses_swapper_for_half_pair_targets() -> None:
    graph = _materialized_graph("CuCuRuRu")

    operation_nodes = [node for node in graph.nodes if isinstance(node, SolverOperationNode)]
    operation_types = [node.operation_type for node in operation_nodes]

    assert operation_types.count("cutter") == 2
    assert operation_types.count("swapper") == 2
    assert operation_types.count("rotate_180") == 2
    assert "stacker" not in operation_types


def test_materialized_graph_builder_keeps_source_counts_fixed_for_mixed_quadrant_batch() -> None:
    graph = _materialized_graph("CuRuSuSu")

    shape_nodes = [node for node in graph.nodes if isinstance(node, SolverShapeNode)]
    operation_nodes = [node for node in graph.nodes if isinstance(node, SolverOperationNode)]
    source_count_by_code: dict[str, int] = {}
    for node in shape_nodes:
        if node.role != "source":
            continue
        source_count_by_code[node.shape_code] = source_count_by_code.get(node.shape_code, 0) + 1

    targets = [node for node in shape_nodes if node.role == "target"]
    assert source_count_by_code == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
    assert len(targets) == 4
    operation_types = [node.operation_type for node in operation_nodes]
    assert operation_types.count("stacker") == 4
    assert operation_types.count("swapper") == 4


def test_materialized_graph_builder_scopes_stackers_to_target_halves() -> None:
    graph = _materialized_graph("CuRuSuWu")

    operation_nodes = [node for node in graph.nodes if isinstance(node, SolverOperationNode)]
    operation_types = [node.operation_type for node in operation_nodes]

    assert operation_types.count("stacker") == 8
    assert operation_types.count("swapper") == 4
