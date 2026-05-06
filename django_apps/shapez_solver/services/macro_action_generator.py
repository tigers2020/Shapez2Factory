"""Generate inventory-search macro actions from registered strategies and DB catalog.

`MacroRecipe.graph_document` is not read by this module; graph-derived planning is
optional and lives in :mod:`graph_document_primitive_chain` (see
``documents/archive/2026-05-completed/recipe-graph-editor/plan_recipe_graph_editor_phases_2026-05-04.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from django.db import DatabaseError

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.search_action import Action
from django_apps.shapez_solver.services.macro_strategy_registry import (
    DEFAULT_MACRO_STRATEGIES,
    MacroStrategy,
)
from django_apps.shapez_solver.services.pattern_catalog_repository import PatternCatalogRepository
from django_apps.shapez_solver.services.pattern_classifier import pattern_signature


@dataclass(frozen=True, slots=True)
class MacroInventorySearchRequestView:
    """순환 import를 피하기 위한 매크로 탐색용 최소 request view."""

    target_code: str
    target_count: int
    source_counts: dict[str, int]


def try_macro_request_view(request: object | None) -> MacroInventorySearchRequestView | None:
    """InventorySearchRequest duck-typed 객체에서 매크로용 view를 만든다."""

    if request is None:
        return None
    target_code = getattr(request, "target_code", None)
    target_count = getattr(request, "target_count", None)
    source_counts = getattr(request, "source_counts", None)
    if not isinstance(target_code, str):
        return None
    if not isinstance(target_count, int):
        return None
    if not isinstance(source_counts, dict):
        return None
    if not all(isinstance(k, str) and isinstance(v, int) for k, v in source_counts.items()):
        return None
    return MacroInventorySearchRequestView(
        target_code=target_code,
        target_count=target_count,
        source_counts=dict(source_counts),
    )


class MacroActionGenerator:
    """등록된 macro strategy에서 inventory search 후보 action을 생성한다."""

    def __init__(self, strategies: tuple[MacroStrategy, ...] | None = None) -> None:
        self.strategies = DEFAULT_MACRO_STRATEGIES if strategies is None else strategies

    def generate(
        self,
        state: InventoryState,
        request: MacroInventorySearchRequestView,
        *,
        target_pattern_signature: str | None = None,
    ) -> tuple[Action, ...]:
        actions: list[Action] = []
        for strategy in self.strategies:
            actions.extend(
                strategy.generate(
                    state,
                    request,
                    target_pattern_signature=target_pattern_signature,
                )
            )
        return tuple(actions)


class CatalogBackedMacroActionGenerator:
    """DB catalog가 활성화한 Python macro strategy만 후보로 생성한다."""

    def __init__(
        self,
        *,
        repository: PatternCatalogRepository | None = None,
        strategies: tuple[MacroStrategy, ...] | None = None,
    ) -> None:
        self.repository = repository or PatternCatalogRepository()
        self.strategies = DEFAULT_MACRO_STRATEGIES if strategies is None else strategies
        self._strategy_codes_by_signature: dict[str, frozenset[str]] = {}

    def generate(
        self,
        state: InventoryState,
        request: MacroInventorySearchRequestView,
        *,
        target_pattern_signature: str | None = None,
    ) -> tuple[Action, ...]:
        sig = (
            target_pattern_signature
            if target_pattern_signature is not None
            else pattern_signature(request.target_code)
        )
        strategy_codes = self._find_strategy_codes(sig)
        if not strategy_codes:
            return ()
        selected_strategies = tuple(
            strategy for strategy in self.strategies if strategy.code in strategy_codes
        )
        actions = MacroActionGenerator(strategies=selected_strategies).generate(
            state,
            request,
            target_pattern_signature=sig,
        )
        return tuple(
            replace(action, macro_source="db") if action.macro_kind else action
            for action in actions
        )

    def _find_strategy_codes(self, signature: str) -> frozenset[str]:
        cached = self._strategy_codes_by_signature.get(signature)
        if cached is not None:
            return cached
        try:
            candidates = self.repository.find_macro_candidates(signature=signature)
        except (DatabaseError, RuntimeError):
            # catalog 조회가 불가능한 환경에서는 내장 macro로 fallback한다.
            candidates = ()
        strategy_codes = frozenset(candidate.strategy_code for candidate in candidates)
        self._strategy_codes_by_signature[signature] = strategy_codes
        return strategy_codes


class CatalogAwareMacroActionGenerator:
    """DB catalog 후보를 먼저 쓰고, 없으면 내장 macro strategy로 fallback한다."""

    def __init__(
        self,
        *,
        repository: PatternCatalogRepository | None = None,
        strategies: tuple[MacroStrategy, ...] | None = None,
    ) -> None:
        self.catalog = CatalogBackedMacroActionGenerator(
            repository=repository,
            strategies=strategies,
        )
        self.fallback = MacroActionGenerator(strategies=strategies)

    def generate(
        self,
        state: InventoryState,
        request: MacroInventorySearchRequestView,
        *,
        target_pattern_signature: str | None = None,
    ) -> tuple[Action, ...]:
        sig = (
            target_pattern_signature
            if target_pattern_signature is not None
            else pattern_signature(request.target_code)
        )
        catalog_actions = self.catalog.generate(state, request, target_pattern_signature=sig)
        if catalog_actions:
            return catalog_actions
        return self.fallback.generate(state, request, target_pattern_signature=sig)


__all__ = [
    "CatalogBackedMacroActionGenerator",
    "CatalogAwareMacroActionGenerator",
    "MacroActionGenerator",
    "MacroInventorySearchRequestView",
    "try_macro_request_view",
]
