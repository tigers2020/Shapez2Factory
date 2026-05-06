from __future__ import annotations

from itertools import combinations_with_replacement

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.search_action import Action
from django_apps.shapez_solver.domain.search_cost import DEFAULT_OPERATION_COST
from django_apps.shapez_solver.services.operation_semantics import apply_operation


class PrimitiveActionGenerator:
    """현재 inventory에서 실행 가능한 primitive action 후보를 만든다."""

    def __init__(self, *, max_inventory_items: int = 12, max_actions: int = 160) -> None:
        self.max_inventory_items = max_inventory_items
        self.max_actions = max_actions

    def generate(self, state: InventoryState) -> tuple[Action, ...]:
        if sum(count for _, count in state.counts) > self.max_inventory_items:
            return ()

        actions: list[Action] = []
        shape_codes = tuple(shape_code for shape_code, _ in state.counts)
        for shape_code in shape_codes:
            actions.extend(self._single_input_actions(shape_code))
            if len(actions) >= self.max_actions:
                return tuple(actions[: self.max_actions])

        for left_shape_code, right_shape_code in combinations_with_replacement(shape_codes, 2):
            actions.extend(self._two_input_actions(state, left_shape_code, right_shape_code))
            if len(actions) >= self.max_actions:
                return tuple(actions[: self.max_actions])

        return tuple(actions)

    def _single_input_actions(self, shape_code: str) -> tuple[Action, ...]:
        actions: list[Action] = []
        for operation in (
            OperationType.ROTATE_CW,
            OperationType.ROTATE_CCW,
            OperationType.ROTATE_180,
            OperationType.CUTTER,
        ):
            try:
                outputs = apply_operation(operation, (shape_code,))
            except ValueError:
                continue
            if _is_noop((shape_code,), outputs):
                continue
            actions.append(
                Action(
                    operation=operation,
                    inputs=(shape_code,),
                    outputs=outputs,
                    cost=DEFAULT_OPERATION_COST,
                )
            )
        return tuple(actions)

    def _two_input_actions(
        self,
        state: InventoryState,
        left_shape_code: str,
        right_shape_code: str,
    ) -> tuple[Action, ...]:
        actions: list[Action] = []
        inputs = (left_shape_code, right_shape_code)
        if not state.can_consume(inputs):
            return ()

        for operation in (OperationType.SWAPPER, OperationType.STACKER):
            try:
                outputs = apply_operation(operation, inputs)
            except ValueError:
                continue
            if _is_noop(inputs, outputs):
                continue
            actions.append(
                Action(
                    operation=operation,
                    inputs=inputs,
                    outputs=outputs,
                    cost=DEFAULT_OPERATION_COST,
                )
            )
        return tuple(actions)


def _is_noop(inputs: tuple[str, ...], outputs: tuple[str, ...]) -> bool:
    return tuple(sorted(inputs)) == tuple(sorted(outputs))
