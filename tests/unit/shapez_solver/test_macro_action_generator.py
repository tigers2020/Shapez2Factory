from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.services.macro_action_generator import (
    MacroActionGenerator,
    MacroInventorySearchRequestView,
)


def test_macro_action_generator_uses_default_strategy_registry_for_checker() -> None:
    request = MacroInventorySearchRequestView(
        target_code="RuCuRuCu",
        target_count=2,
        source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1},
    )
    state = InventoryState.from_counts(request.source_counts)

    actions = MacroActionGenerator().generate(state, request)

    assert tuple(action.macro_kind for action in actions) == ("CHECKER_PAIR",)


def test_macro_action_generator_uses_default_strategy_registry_for_abcc_batch() -> None:
    request = MacroInventorySearchRequestView(
        target_code="CuRuSuSu",
        target_count=4,
        source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
    )
    state = InventoryState.from_counts(request.source_counts)

    actions = MacroActionGenerator().generate(state, request)

    assert tuple(action.macro_kind for action in actions) == ("ABCC_BATCH",)
    assert len(actions[0].primitive_chain or ()) == 21


def test_macro_action_generator_allows_catalog_to_disable_strategies() -> None:
    request = MacroInventorySearchRequestView(
        target_code="CuRuSuSu",
        target_count=4,
        source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
    )
    state = InventoryState.from_counts(request.source_counts)

    actions = MacroActionGenerator(strategies=()).generate(state, request)

    assert actions == ()
