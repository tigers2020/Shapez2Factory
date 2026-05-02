from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.services.shape_render_scene import build_shape_render_scene
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.recipe import (
    OperationRecipe,
    RecipeRef,
    SolvedRecipe,
    SourceRecipe,
)
from django_apps.shapez_solver.dto.solver_graph import (
    ShapeNodeRole,
    SolverGraph,
    SolverGraphEdge,
    SolverOperationNode,
    SolverShapeNode,
)


@dataclass(slots=True)
class _ShapeNodeDraft:
    id: str
    role: ShapeNodeRole
    shape_code: str
    label: str
    reused_count: int


class GraphBuilder:
    def build(self, solved: SolvedRecipe) -> SolverGraph:
        target_shape = solved.ref.shape.canonical_code
        shape_reference_counts: dict[str, int] = {}
        produced_shapes: set[str] = set()
        shape_drafts: dict[str, _ShapeNodeDraft] = {}
        operation_nodes: list[SolverOperationNode] = []
        edges: list[SolverGraphEdge] = []

        def get_shape_node(
            shape_code: str,
            role: ShapeNodeRole,
            label: str,
        ) -> _ShapeNodeDraft:
            resolved_role = "target" if shape_code == target_shape else role
            draft = shape_drafts.get(shape_code)
            if draft is None:
                draft = _ShapeNodeDraft(
                    id=f"shape:{shape_code}",
                    role=resolved_role,
                    shape_code=shape_code,
                    label=label,
                    reused_count=max(0, shape_reference_counts.get(shape_code, 0) - 1),
                )
                shape_drafts[shape_code] = draft
                return draft
            if draft.role != "target" and resolved_role == "target":
                draft.role = "target"
                draft.label = label
            return draft

        for recipe in solved.recipes:
            if isinstance(recipe, SourceRecipe):
                shape_reference_counts[recipe.shape.canonical_code] = (
                    shape_reference_counts.get(recipe.shape.canonical_code, 0) + 1
                )
                continue
            for input_ref in recipe.inputs:
                shape_reference_counts[input_ref.shape.canonical_code] = (
                    shape_reference_counts.get(input_ref.shape.canonical_code, 0) + 1
                )
            for output in recipe.outputs:
                shape_reference_counts[output.canonical_code] = (
                    shape_reference_counts.get(output.canonical_code, 0) + 1
                )

        for recipe in solved.recipes:
            if isinstance(recipe, SourceRecipe):
                get_shape_node(recipe.shape.canonical_code, "source", recipe.label)
                continue

            definition = OPERATION_CATALOG[recipe.operation_type]
            operation_node = SolverOperationNode(
                id=recipe.id,
                operation_type=definition.type.value,
                label=recipe.label,
                icon=definition.icon,
                input_count=definition.input_count,
                output_count=len(recipe.outputs),
                description=recipe.description,
            )
            operation_nodes.append(operation_node)

            for index, input_ref in enumerate(recipe.inputs):
                input_role: ShapeNodeRole = (
                    "intermediate"
                    if input_ref.shape.canonical_code in produced_shapes
                    else "source"
                )
                shape_node = get_shape_node(
                    input_ref.shape.canonical_code,
                    input_role,
                    _ref_label(input_ref),
                )
                slot = _slot_name(index)
                edges.append(
                    SolverGraphEdge(
                        from_id=shape_node.id,
                        to_id=operation_node.id,
                        kind="input",
                        slot=slot,
                        label=f"Input {slot}",
                    )
                )

            for index, output in enumerate(recipe.outputs):
                produced_shapes.add(output.canonical_code)
                output_role: ShapeNodeRole = (
                    "target" if output.canonical_code == target_shape else "intermediate"
                )
                shape_node = get_shape_node(
                    output.canonical_code,
                    output_role,
                    _output_label(recipe, index, solved.ref),
                )
                slot = _slot_name(index)
                edge_label = f"Output {slot}"
                if (
                    output.canonical_code != solved.ref.shape.canonical_code
                    and not _output_is_used(
                        solved.recipes,
                        RecipeRef(recipe_id=recipe.id, output_index=index, shape=output),
                    )
                ):
                    edge_label = f"Output {slot} (unused)"
                edges.append(
                    SolverGraphEdge(
                        from_id=operation_node.id,
                        to_id=shape_node.id,
                        kind="output",
                        slot=slot,
                        label=edge_label,
                    )
                )

        shape_nodes = tuple(
            SolverShapeNode(
                id=draft.id,
                role=draft.role,
                shape_code=draft.shape_code,
                label=draft.label,
                preview_scene=_serialize_scene(draft.shape_code),
                reused_count=draft.reused_count,
            )
            for draft in shape_drafts.values()
        )
        return SolverGraph(nodes=(*shape_nodes, *operation_nodes), edges=tuple(edges))


def _output_is_used(
    recipes: tuple[SourceRecipe | OperationRecipe, ...],
    target: RecipeRef,
) -> bool:
    return any(
        isinstance(recipe, OperationRecipe)
        and any(
            input_ref.recipe_id == target.recipe_id
            and input_ref.output_index == target.output_index
            for input_ref in recipe.inputs
        )
        for recipe in recipes
    )


def _serialize_scene(shape_code: str) -> dict[str, object]:
    from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list

    scene = build_shape_render_scene(parse_shape_code_list(shape_code)[0])
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


def _slot_name(index: int) -> str:
    return ("A", "B", "C", "D")[index] if index < 4 else str(index + 1)


def _ref_label(ref: RecipeRef) -> str:
    return "Target" if ref.output_index == 0 else f"Shape {ref.output_index + 1}"


def _output_label(recipe: OperationRecipe, index: int, selected_ref: RecipeRef) -> str:
    if recipe.id == selected_ref.recipe_id and index == selected_ref.output_index:
        return "Target"
    return f"Output {_slot_name(index)}"
