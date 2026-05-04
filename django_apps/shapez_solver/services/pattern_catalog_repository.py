from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_solver.models import MacroRecipe


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
    """DB catalog에서 조회한 macro strategy 후보 메타데이터."""

    macro_code: str
    strategy_code: str
    family_code: str
    estimated_operation_cost: int
    estimated_stage_cost: int
    estimated_waste_cost: int
    priority: int
    steps: tuple[PatternMacroStepCandidate, ...] = ()


class PatternCatalogRepository:
    """Pattern DB에서 활성 macro 후보를 조회한다."""

    def find_macro_candidates(self, *, signature: str) -> tuple[PatternMacroCandidate, ...]:
        recipes = (
            MacroRecipe.objects.select_related("family")
            .prefetch_related("steps")
            .filter(is_active=True, family__is_active=True, family__signature=signature)
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
                steps=tuple(
                    PatternMacroStepCandidate(
                        step_index=step.step_index,
                        operation=step.operation,
                        input_slots=tuple(str(item) for item in step.input_slots),
                        output_slots=tuple(str(item) for item in step.output_slots),
                        note=step.note,
                    )
                    for step in recipe.steps.all()
                ),
            )
            for recipe in recipes
        )


__all__ = [
    "PatternCatalogRepository",
    "PatternMacroCandidate",
    "PatternMacroStepCandidate",
]
