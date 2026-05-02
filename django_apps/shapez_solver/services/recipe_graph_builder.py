from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_render_scene import build_shape_render_scene
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    RecipeRef,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)


@dataclass(frozen=True, slots=True)
class _GraphBuildState:
    nodes: list[SolverGraphNode]
    edges: list[SolverGraphEdge]
    seen_shape_nodes: set[str]
    final_key: str
    used_output_keys: set[str]
    reused_counts: dict[str, int]
    target_count: int


@dataclass(frozen=True, slots=True)
class RecipeGraphBuilder:
    def build(
        self,
        solved: SolvedRecipe,
        *,
        target_count: int = 1,
        base_demands: tuple[object, ...] = (),
    ) -> SolverGraph:
        del base_demands
        state = _build_state(solved, target_count=target_count)

        for recipe in solved.recipes:
            if isinstance(recipe, SourceRecipe):
                _append_source_shape_node(state, recipe)
                continue
            if not isinstance(recipe, OperationRecipe):
                continue

            _append_operation_node(state, recipe)
            _append_input_edges(state, recipe)
            _append_output_shape_nodes_and_edges(state, recipe)

        return SolverGraph(nodes=tuple(state.nodes), edges=tuple(state.edges))


def _build_state(solved: SolvedRecipe, *, target_count: int) -> _GraphBuildState:
    final_key = _ref_key(solved.ref)
    return _GraphBuildState(
        nodes=[],
        edges=[],
        seen_shape_nodes=set(),
        final_key=final_key,
        used_output_keys=_compute_used_output_keys(solved, final_key),
        reused_counts=_compute_reused_counts(solved),
        target_count=target_count,
    )


def _compute_used_output_keys(solved: SolvedRecipe, final_key: str) -> set[str]:
    used_output_keys = {
        _ref_key(recipe_input)
        for recipe in solved.recipes
        if isinstance(recipe, OperationRecipe)
        for recipe_input in recipe.inputs
    }
    used_output_keys.add(final_key)
    return used_output_keys


def _append_source_shape_node(state: _GraphBuildState, recipe: SourceRecipe) -> None:
    node_id = _shape_node_id(recipe.id, 0)
    if node_id in state.seen_shape_nodes:
        return

    recipe_key = f"{recipe.id}:0"
    is_target = state.final_key == recipe_key
    node_key = state.final_key if is_target else recipe_key
    state.nodes.append(
        SolverShapeNode(
            id=node_id,
            role="target" if is_target else "source",
            shape_code=recipe.shape.canonical_code,
            label=_target_label(state.target_count) if is_target else recipe.label,
            preview_scene=_serialize_shape_preview(recipe.shape),
            reused_count=state.reused_counts.get(node_key, 0),
            quantity=state.target_count if is_target else 1,
        )
    )
    state.seen_shape_nodes.add(node_id)


def _append_operation_node(state: _GraphBuildState, recipe: OperationRecipe) -> None:
    operation = OPERATION_CATALOG[recipe.operation_type]
    state.nodes.append(
        SolverOperationNode(
            id=recipe.id,
            operation_type=recipe.operation_type.value,
            label=recipe.label,
            icon=operation.icon,
            input_count=operation.input_count,
            output_count=operation.output_count,
            description=recipe.description,
        )
    )


def _append_input_edges(state: _GraphBuildState, recipe: OperationRecipe) -> None:
    for index, recipe_input in enumerate(recipe.inputs):
        input_shape_id = _shape_node_id(recipe_input.recipe_id, recipe_input.output_index)
        slot_label = _slot_label(index)
        state.edges.append(
            SolverGraphEdge(
                from_id=input_shape_id,
                to_id=recipe.id,
                kind="input",
                slot=slot_label,
                label=slot_label,
            )
        )


def _append_output_shape_nodes_and_edges(state: _GraphBuildState, recipe: OperationRecipe) -> None:
    for output_index, output_shape in enumerate(recipe.outputs):
        output_key = f"{recipe.id}:{output_index}"
        output_node_id = _shape_node_id(recipe.id, output_index)
        _append_output_shape_node(
            state,
            output_key=output_key,
            output_node_id=output_node_id,
            output_shape=output_shape,
        )
        state.edges.append(
            SolverGraphEdge(
                from_id=recipe.id,
                to_id=output_node_id,
                kind="output",
                slot=_output_label(output_index),
                label=_output_edge_label(output_index, output_key in state.used_output_keys),
            )
        )


def _append_output_shape_node(
    state: _GraphBuildState,
    *,
    output_key: str,
    output_node_id: str,
    output_shape: Shape,
) -> None:
    if output_node_id in state.seen_shape_nodes:
        return

    is_target = output_key == state.final_key
    state.nodes.append(
        SolverShapeNode(
            id=output_node_id,
            role="target" if is_target else "intermediate",
            shape_code=output_shape.canonical_code,
            label=_target_label(state.target_count) if is_target else "Shape",
            preview_scene=_serialize_shape_preview(output_shape),
            reused_count=state.reused_counts.get(output_key, 0),
            quantity=state.target_count if is_target else 1,
        )
    )
    state.seen_shape_nodes.add(output_node_id)


def _compute_reused_counts(solved: SolvedRecipe) -> dict[str, int]:
    counts: dict[str, int] = {}
    for recipe in solved.recipes:
        if not isinstance(recipe, OperationRecipe):
            continue
        for recipe_input in recipe.inputs:
            key = _ref_key(recipe_input)
            counts[key] = counts.get(key, 0) + 1
    return {key: max(count - 1, 0) for key, count in counts.items() if count > 1}


def _serialize_shape_preview(shape: Shape) -> dict[str, object]:
    scene = build_shape_render_scene(shape)
    return {
        "normalized_code": scene.normalized_code,
        "cells": [
            {
                "layer_index": cell.layer_index,
                "quadrant_index": cell.quadrant_index,
                "position": cell.position.value,
                "shape_code": cell.shape_code,
                "color_code": cell.color_code,
                "shape_kind": cell.shape_kind,
                "color_kind": cell.color_kind,
                "mesh_key": cell.mesh_key,
                "material_key": cell.material_key,
                "transform_key": cell.transform_key,
            }
            for cell in scene.cells
        ],
    }


def _shape_node_id(recipe_id: str, output_index: int) -> str:
    return f"{recipe_id}:shape:{output_index}"


def _ref_key(ref: RecipeRef) -> str:
    return f"{ref.recipe_id}:{ref.output_index}"


def _slot_label(index: int) -> str:
    return f"Input {chr(ord('A') + index)}"


def _output_label(index: int) -> str:
    return f"Output {chr(ord('A') + index)}"


def _output_edge_label(index: int, is_used: bool) -> str:
    label = _output_label(index)
    return label if is_used else f"{label} (unused)"


def _target_label(target_count: int) -> str:
    return f"Target x{target_count}" if target_count > 1 else "Target"
