"""MacroRecipe catalog JSON / recipe detail serialization (staff UI + APIs)."""

from __future__ import annotations

from typing import Any

from django.db.models import Prefetch
from django.templatetags.static import static

from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.models import (
    MacroRecipe,
    MacroRecipeCompiledBoundary,
    MacroRecipeStep,
    PatternFamily,
)
from django_apps.shapez_solver.ports.graph_preview import (
    GraphPreviewRenderer,
    NoopGraphPreviewRenderer,
)
from django_apps.shapez_solver.services.macro_recipe_graph_visual import (
    serialize_macro_recipe_visual,
)
from django_apps.shapez_solver.services.recipe_graph_constants import RECIPE_GRAPH_ENGINE_OPERATIONS
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    try_pattern_macro_step_rows_from_graph_document,
)

MACRO_RECIPE_DETAIL_PREFETCHES = (
    Prefetch("steps", queryset=MacroRecipeStep.objects.order_by("step_index")),
    Prefetch(
        "compiled_boundaries",
        queryset=MacroRecipeCompiledBoundary.objects.order_by("boundary", "graph_shape_id"),
    ),
)


def allowed_strategy_codes() -> tuple[str, ...]:
    return ("ABCC_BATCH", "CHECKER_PAIR")


def operation_choices() -> tuple[tuple[str, str], ...]:
    return tuple((item.value, item.name) for item in OperationType)


def catalog_operations_payload() -> list[dict[str, str]]:
    """스태프 UI·팔레트용: 각 연산의 정적 아이콘 URL을 포함한다."""
    rows: list[dict[str, str]] = []
    for val, name in operation_choices():
        icon_url = ""
        try:
            ot = OperationType(val)
            icon_url = static(f"web/images/operations/{OPERATION_CATALOG[ot].icon}")
        except (ValueError, KeyError):
            icon_url = ""
        rows.append({"value": val, "label": name, "icon": icon_url})
    return rows


def _serialize_step(step: MacroRecipeStep) -> dict[str, Any]:
    return {
        "id": step.id,
        "step_index": step.step_index,
        "operation": step.operation,
        "input_slots": step.input_slots,
        "output_slots": step.output_slots,
        "note": step.note,
    }


def _serialize_compiled_boundary(row: MacroRecipeCompiledBoundary) -> dict[str, Any]:
    return {
        "graph_shape_id": row.graph_shape_id,
        "pattern_signature": row.pattern_signature,
        "boundary": row.boundary,
    }


def serialize_recipe(
    recipe: MacroRecipe,
    *,
    sync_png: bool = True,
    preview_renderer: GraphPreviewRenderer | None = None,
) -> dict[str, Any]:
    steps = sorted(recipe.steps.all(), key=lambda s: s.step_index)
    visual_graph = None
    renderer = preview_renderer if preview_renderer is not None else NoopGraphPreviewRenderer()
    if recipe.graph_document:
        try:
            visual_graph = serialize_macro_recipe_visual(
                recipe.graph_document,
                sync_png=sync_png,
                preview_renderer=renderer,
            )
        except (ValueError, TypeError, KeyError):
            visual_graph = None
    lab_rows = try_pattern_macro_step_rows_from_graph_document(recipe.graph_document)
    return {
        "id": recipe.id,
        "family_id": recipe.family_id,
        "family_code": recipe.family.code,
        "family_signature": recipe.family.signature,
        "code": recipe.code,
        "strategy_code": recipe.strategy_code,
        "name": recipe.name,
        "estimated_operation_cost": recipe.estimated_operation_cost,
        "estimated_stage_cost": recipe.estimated_stage_cost,
        "estimated_waste_cost": recipe.estimated_waste_cost,
        "priority": recipe.priority,
        "is_active": recipe.is_active,
        "schema_version": recipe.schema_version,
        "graph_document": recipe.graph_document,
        "visual_graph": visual_graph,
        "pattern_lab_steps": lab_rows,
        "steps": [_serialize_step(s) for s in steps],
        "compiled_boundaries": [
            _serialize_compiled_boundary(b)
            for b in sorted(
                recipe.compiled_boundaries.all(),
                key=lambda x: (x.boundary, x.graph_shape_id),
            )
        ],
    }


def build_catalog_snapshot(*, sync_png: bool = False) -> dict[str, Any]:
    """Bulk catalog JSON/HTML. Default ``sync_png=False`` avoids Playwright per node (timeouts)."""
    families = PatternFamily.objects.order_by("priority", "code").values(
        "id",
        "code",
        "name",
        "signature",
        "is_active",
    )
    recipes = MacroRecipe.objects.select_related("family").prefetch_related(
        *MACRO_RECIPE_DETAIL_PREFETCHES,
    )
    return {
        "families": list(families),
        "recipes": [
            serialize_recipe(r, sync_png=sync_png) for r in recipes.order_by("priority", "code")
        ],
        "strategy_codes": list(allowed_strategy_codes()),
        "operations": catalog_operations_payload(),
        "recipe_graph_engine_operations": sorted(RECIPE_GRAPH_ENGINE_OPERATIONS),
    }
