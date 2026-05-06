from __future__ import annotations

from typing import Protocol

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.search_action import Action
from django_apps.shapez_solver.services.action_generator import PrimitiveActionGenerator
from django_apps.shapez_solver.services.macro_action_generator import (
    MacroActionGenerator,
    MacroInventorySearchRequestView,
    try_macro_request_view,
)
from django_apps.shapez_solver.services.pattern_classifier import pattern_signature


class _MacroGenerator(Protocol):
    def generate(
        self,
        state: InventoryState,
        request: MacroInventorySearchRequestView,
        *,
        target_pattern_signature: str | None = None,
    ) -> tuple[Action, ...]: ...


class CombinedActionGenerator:
    """Primitive 후보와 매크로 후보를 합친다."""

    def __init__(
        self,
        primitives: PrimitiveActionGenerator | None = None,
        macros: _MacroGenerator | None = None,
    ) -> None:
        self.primitives = primitives or PrimitiveActionGenerator()
        self.macros = macros or MacroActionGenerator()

    def generate(
        self,
        state: InventoryState,
        request: object | None = None,
    ) -> tuple[Action, ...]:
        macro_view = try_macro_request_view(request)
        if macro_view is None:
            return self.primitives.generate(state)
        sig = pattern_signature(macro_view.target_code)
        macro_actions = self.macros.generate(state, macro_view, target_pattern_signature=sig)
        if macro_actions:
            return macro_actions
        return self.primitives.generate(state)
