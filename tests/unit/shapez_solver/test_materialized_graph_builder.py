from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.factory_demand import BaseDemand
from django_apps.shapez_solver.domain.recipe import (
    RecipeCost,
    RecipeRef,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.dto.solver_graph import SolverOperationNode, SolverShapeNode
from django_apps.shapez_solver.services.materialized_graph_builder import MaterializedGraphBuilder


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def _source_only_solved(code: str) -> SolvedRecipe:
    source = SourceRecipe(id=f"source:{code}", shape=_shape(code))
    return SolvedRecipe(
        ref=RecipeRef(recipe_id=source.id, output_index=0, shape=source.shape),
        recipes=(source,),
        cost=RecipeCost(operations=0, sources=1, depth=1, reused_nodes=0),
    )


def test_materialized_graph_builder_builds_fixed_source_batch_for_half_targets() -> None:
    graph = MaterializedGraphBuilder().build(
        _source_only_solved("RuRu----"),
        target_count=2,
        base_demands=(
            BaseDemand(
                base_shape_code="RuRuRuRu",
                quadrants_per_target=2,
                total_quadrants=4,
                full_source_count=1,
            ),
        ),
    )

    assert graph is not None
    shape_nodes = [node for node in graph.nodes if isinstance(node, SolverShapeNode)]
    operation_nodes = [node for node in graph.nodes if isinstance(node, SolverOperationNode)]

    sources = [node for node in shape_nodes if node.role == "source"]
    targets = [node for node in shape_nodes if node.role == "target"]
    consumed = [node for node in shape_nodes if node.produced_state == "consumed"]

    assert len(sources) == 1
    assert len(targets) == 2
    assert len(operation_nodes) >= 5
    assert consumed


def test_materialized_graph_builder_keeps_source_counts_fixed_for_mixed_quadrant_batch() -> None:
    graph = MaterializedGraphBuilder().build(
        _source_only_solved("CuRuSuSu"),
        target_count=4,
        base_demands=(
            BaseDemand("CuCuCuCu", quadrants_per_target=1, total_quadrants=4, full_source_count=1),
            BaseDemand("RuRuRuRu", quadrants_per_target=1, total_quadrants=4, full_source_count=1),
            BaseDemand("SuSuSuSu", quadrants_per_target=2, total_quadrants=8, full_source_count=2),
        ),
    )

    assert graph is not None
    shape_nodes = [node for node in graph.nodes if isinstance(node, SolverShapeNode)]
    source_count_by_code: dict[str, int] = {}
    for node in shape_nodes:
        if node.role != "source":
            continue
        source_count_by_code[node.shape_code] = source_count_by_code.get(node.shape_code, 0) + 1

    targets = [node for node in shape_nodes if node.role == "target"]
    assert source_count_by_code == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
    assert len(targets) == 4
