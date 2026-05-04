from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.search_action import Action
from django_apps.shapez_solver.domain.search_cost import DEFAULT_OPERATION_COST
from django_apps.shapez_solver.services.action_applier import apply_action
from django_apps.shapez_solver.services.operation_semantics import rotate, swap


def test_inventory_state_is_hashable_and_normalizes_counts() -> None:
    state = InventoryState.from_counts({"CuCuCuCu": 1, "RcRcRcRc": 0, "RuRuRuRu": 2})

    assert state == InventoryState(counts=(("CuCuCuCu", 1), ("RuRuRuRu", 2)))
    assert {state: "cached"}[state] == "cached"


def test_apply_action_consumes_inputs_and_produces_outputs() -> None:
    state = InventoryState.from_counts({"RcRcRcRc": 1, "CuCuCuCu": 1})
    action = Action(
        operation=OperationType.SWAPPER,
        inputs=("RcRcRcRc", "CuCuCuCu"),
        outputs=("RcRcCuCu", "CuCuRcRc"),
        cost=DEFAULT_OPERATION_COST,
    )

    result = apply_action(state, action)

    assert result.to_dict() == {"RcRcCuCu": 1, "CuCuRcRc": 1}


def test_operation_semantics_keeps_swapper_as_two_output_action() -> None:
    outputs = swap("RcRcRcRc", "CuCuCuCu")

    assert outputs == ("RcRcCuCu", "CuCuRcRc")


def test_operation_semantics_rotates_canonical_codes() -> None:
    assert rotate("RcRcCuCu", OperationType.ROTATE_CW) == ("CuRcRcCu",)
