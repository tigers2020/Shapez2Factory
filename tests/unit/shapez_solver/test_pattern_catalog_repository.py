import pytest

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily
from django_apps.shapez_solver.services.combined_action_generator import CombinedActionGenerator
from django_apps.shapez_solver.services.inventory_search_solver import (
    InventorySearchRequest,
    InventorySearchSolver,
)
from django_apps.shapez_solver.services.macro_action_generator import (
    CatalogBackedMacroActionGenerator,
    MacroInventorySearchRequestView,
)
from django_apps.shapez_solver.services.pattern_catalog_repository import PatternCatalogRepository


@pytest.mark.django_db
def test_pattern_catalog_repository_returns_active_macro_candidates() -> None:
    family = PatternFamily.objects.create(
        code="abcc",
        name="ABCC",
        signature="ABCC",
        priority=10,
    )
    MacroRecipe.objects.create(
        family=family,
        code="abcc-batch",
        strategy_code="ABCC_BATCH",
        name="ABCC Batch",
        estimated_operation_cost=21,
        priority=5,
    )
    MacroRecipeStep.objects.create(
        macro=MacroRecipe.objects.get(code="abcc-batch"),
        step_index=1,
        operation="stacker",
        input_slots=["AB_half", "CC_half"],
        output_slots=["ABCC"],
        note="표시용 step",
    )

    candidates = PatternCatalogRepository().find_macro_candidates(signature="ABCC")

    assert len(candidates) == 1
    assert candidates[0].macro_code == "abcc-batch"
    assert candidates[0].strategy_code == "ABCC_BATCH"
    assert candidates[0].family_code == "abcc"
    assert candidates[0].steps[0].operation == "stacker"
    assert candidates[0].steps[0].input_slots == ("AB_half", "CC_half")


@pytest.mark.django_db
def test_catalog_backed_macro_action_generator_uses_db_enabled_strategy() -> None:
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
    request = MacroInventorySearchRequestView(
        target_code="CuRuSuSu",
        target_count=4,
        source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
    )
    state = InventoryState.from_counts(request.source_counts)

    actions = CatalogBackedMacroActionGenerator().generate(state, request)

    assert tuple(action.macro_kind for action in actions) == ("ABCC_BATCH",)


@pytest.mark.django_db
def test_catalog_backed_macro_action_generator_returns_no_actions_without_db_match() -> None:
    request = MacroInventorySearchRequestView(
        target_code="CuRuSuSu",
        target_count=4,
        source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
    )
    state = InventoryState.from_counts(request.source_counts)

    actions = CatalogBackedMacroActionGenerator().generate(state, request)

    assert actions == ()


@pytest.mark.django_db
def test_catalog_backed_macro_generator_can_be_injected_into_inventory_search() -> None:
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
    action_generator = CombinedActionGenerator(macros=CatalogBackedMacroActionGenerator())

    plan = InventorySearchSolver(action_generator).solve(
        InventorySearchRequest(
            target_code="CuRuSuSu",
            target_count=4,
            source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
            max_states=100,
            max_steps=28,
        )
    )

    assert plan.final_inventory.get("CuRuSuSu") == 4
    assert "ABCC_BATCH" in plan.used_macro_kinds
    assert "ABCC_BATCH:db" in plan.used_macro_sources
