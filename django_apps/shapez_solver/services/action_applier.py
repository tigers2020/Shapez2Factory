from __future__ import annotations

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.search_action import Action


def apply_action(state: InventoryState, action: Action) -> InventoryState:
    """Action의 input을 소비하고 output을 inventory에 더한다."""

    if action.primitive_chain:
        next_state = state
        for sub in action.primitive_chain:
            next_state = apply_action(next_state, sub)
        return next_state
    if not state.can_consume(action.inputs):
        raise ValueError("action inputs are not available in inventory")
    return state.consume_and_produce(action.inputs, action.outputs)
