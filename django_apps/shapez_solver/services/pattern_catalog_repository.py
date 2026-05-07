"""DB-backed pattern family / macro recipe catalog for Pattern Lab.

Catalog matches `MacroRecipe` / `PatternFamily` rows by pattern signature.
`MacroRecipe.graph_document` is used for step metadata (see recompute helpers), not as a search graph here.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Exists, OuterRef

from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeCompiledBoundary
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    try_pattern_macro_step_rows_from_graph_document,
)


@dataclass(frozen=True, slots=True)
class PatternMacroStepCandidate:
    """Pattern Lab에 표시할 macro recipe step 메타데이터."""

    step_index: int
    operation: str
    input_slots: tuple[str, ...]
    output_slots: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class PatternMacroCandidate:
    """DB catalog에서 조회한 macro strategy 후보 메타데이터.

    ``lab_step_source``가 ``graph_document``이면 Pattern Lab에 보이는 스텝 행이
    ``graph_document``에서 파생된 것이다(아니면 DB ``MacroRecipeStep``).
    """

    macro_code: str
    strategy_code: str
    family_code: str
    estimated_operation_cost: int
    estimated_stage_cost: int
    estimated_waste_cost: int
    priority: int
    steps: tuple[PatternMacroStepCandidate, ...] = ()
    lab_step_source: str = "database"


def _pattern_lab_steps_bundle(
    recipe: MacroRecipe,
) -> tuple[tuple[PatternMacroStepCandidate, ...], str]:
    rows = try_pattern_macro_step_rows_from_graph_document(recipe.graph_document)
    if rows is not None:
        steps = tuple(
            PatternMacroStepCandidate(
                step_index=int(s["step_index"]),
                operation=str(s["operation"]),
                input_slots=tuple(str(x) for x in s["input_slots"]),
                output_slots=tuple(str(x) for x in s["output_slots"]),
                note=str(s.get("note") or ""),
            )
            for s in rows
        )
        return steps, "graph_document"
    steps = tuple(
        PatternMacroStepCandidate(
            step_index=step.step_index,
            operation=step.operation,
            input_slots=tuple(str(item) for item in step.input_slots),
            output_slots=tuple(str(item) for item in step.output_slots),
            note=step.note,
        )
        for step in recipe.steps.all()
    )
    return steps, "database"


class PatternCatalogRepository:
    """Pattern DB에서 활성 macro 후보를 조회한다."""

    def find_macro_candidates(self, *, signature: str) -> tuple[PatternMacroCandidate, ...]:
        has_boundary = MacroRecipeCompiledBoundary.objects.filter(macro_id=OuterRef("pk"))
        end_matches_sig = MacroRecipeCompiledBoundary.objects.filter(
            macro_id=OuterRef("pk"),
            boundary=MacroRecipeCompiledBoundary.Boundary.END,
            pattern_signature=signature,
        )
        recipes = (
            MacroRecipe.objects.select_related("family")
            .prefetch_related("steps", "compiled_boundaries")
            .filter(is_active=True, family__is_active=True, family__signature=signature)
            .filter(~Exists(has_boundary) | Exists(end_matches_sig))
            .order_by("priority", "code")
        )
        return tuple(
            PatternMacroCandidate(
                macro_code=recipe.code,
                strategy_code=recipe.strategy_code,
                family_code=recipe.family.code,
                estimated_operation_cost=recipe.estimated_operation_cost,
                estimated_stage_cost=recipe.estimated_stage_cost,
                estimated_waste_cost=recipe.estimated_waste_cost,
                priority=recipe.priority,
                steps=steps,
                lab_step_source=source,
            )
            for recipe in recipes
            for steps, source in (_pattern_lab_steps_bundle(recipe),)
        )
