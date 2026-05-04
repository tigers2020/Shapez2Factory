from __future__ import annotations

import time
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Protocol

from django_apps.shapez_solver.domain.batch_plan import BatchPlan
from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.search_action import Action, OperationRun
from django_apps.shapez_solver.domain.search_cost import ZERO_SEARCH_COST, SearchCost
from django_apps.shapez_solver.services.action_applier import apply_action
from django_apps.shapez_solver.services.combined_action_generator import CombinedActionGenerator

MAX_SEARCH_COST = SearchCost(999_999, 999_999, 999_999, 999_999)


class InventorySearchError(Exception):
    """Inventory search가 plan을 찾지 못했을 때 발생한다."""


@dataclass(frozen=True, slots=True)
class InventorySearchRequest:
    target_code: str
    target_count: int
    source_counts: dict[str, int]
    max_states: int = 10_000
    max_steps: int = 24
    deadline_monotonic: float | None = None


@dataclass(frozen=True, slots=True)
class _ParentPointer:
    previous_state: InventoryState
    action: Action


class _ActionGenerator(Protocol):
    def generate(
        self,
        state: InventoryState,
        request: InventorySearchRequest | None = None,
    ) -> tuple[Action, ...]: ...


class InventorySearchSolver:
    """Batch-aware inventory 상태 공간을 uniform-cost search로 탐색한다."""

    def __init__(self, action_generator: _ActionGenerator | None = None) -> None:
        self.action_generator = action_generator or CombinedActionGenerator()

    def _try_macro_shortcut(
        self,
        request: InventorySearchRequest,
        *,
        state: InventoryState,
        base_cost: SearchCost,
        base_steps: int,
    ) -> BatchPlan | None:
        """배치 매크로는 primitive보다 누적 비용이 커 Dijkstra에서 후순위이므로 선제 시도한다."""

        for action in self.action_generator.generate(state, request):
            if not action.macro_kind or not action.primitive_chain:
                continue
            chain_len = len(action.primitive_chain)
            if base_steps + chain_len > request.max_steps:
                continue
            next_state = apply_action(state, action)
            if next_state.count(request.target_code) < request.target_count:
                continue
            parents = {next_state: _ParentPointer(previous_state=state, action=action)}
            total_cost = base_cost + action.cost
            return self._build_plan(request, next_state, parents, total_cost, states_explored=1)
        return None

    def solve(self, request: InventorySearchRequest) -> BatchPlan:
        if request.deadline_monotonic is not None and time.monotonic() > request.deadline_monotonic:
            raise InventorySearchError(
                f"deadline exceeded for {request.target_code} x{request.target_count}"
            )

        initial_state = InventoryState.from_counts(request.source_counts)
        macro_plan = self._try_macro_shortcut(
            request,
            state=initial_state,
            base_cost=ZERO_SEARCH_COST,
            base_steps=0,
        )
        if macro_plan is not None:
            return macro_plan

        best_costs: dict[InventoryState, SearchCost] = {initial_state: ZERO_SEARCH_COST}
        parents: dict[InventoryState, _ParentPointer] = {}
        step_counts: dict[InventoryState, int] = {initial_state: 0}
        queue: list[tuple[SearchCost, int, InventoryState]] = []
        sequence = 0
        heappush(queue, (ZERO_SEARCH_COST, sequence, initial_state))
        states_explored = 0

        while queue and states_explored < request.max_states:
            if request.deadline_monotonic is not None:
                if time.monotonic() > request.deadline_monotonic:
                    raise InventorySearchError(
                        f"deadline exceeded for {request.target_code} x{request.target_count}"
                    )

            current_cost, _, current_state = heappop(queue)
            if current_cost != best_costs[current_state]:
                continue
            states_explored += 1

            if current_state.count(request.target_code) >= request.target_count:
                return self._build_plan(
                    request, current_state, parents, current_cost, states_explored
                )

            current_steps = step_counts[current_state]
            if current_steps >= request.max_steps:
                continue

            for action in self.action_generator.generate(current_state, request):
                chain_len = len(action.primitive_chain) if action.primitive_chain else 1
                if current_steps + chain_len > request.max_steps:
                    continue
                next_state = apply_action(current_state, action)
                next_cost = current_cost + action.cost
                if next_cost >= best_costs.get(next_state, MAX_SEARCH_COST):
                    continue
                best_costs[next_state] = next_cost
                parents[next_state] = _ParentPointer(previous_state=current_state, action=action)
                step_counts[next_state] = current_steps + chain_len
                sequence += 1
                heappush(queue, (next_cost, sequence, next_state))

        raise InventorySearchError(
            f"no batch plan found for {request.target_code} x{request.target_count}"
        )

    def _flatten_actions(self, actions: list[Action]) -> tuple[OperationRun, ...]:
        runs: list[OperationRun] = []
        stage_index = 0
        for action in actions:
            if action.primitive_chain:
                for offset, sub in enumerate(action.primitive_chain):
                    stage_index += 1
                    runs.append(
                        OperationRun(
                            id=f"run-{len(runs) + 1}",
                            operation=sub.operation,
                            inputs=sub.inputs,
                            outputs=sub.outputs,
                            stage_index=stage_index,
                            run_index=len(runs) + 1,
                            macro_kind=action.macro_kind if offset == 0 else "",
                            macro_source=action.macro_source if offset == 0 else "",
                        )
                    )
            else:
                stage_index += 1
                runs.append(
                    OperationRun(
                        id=f"run-{len(runs) + 1}",
                        operation=action.operation,
                        inputs=action.inputs,
                        outputs=action.outputs,
                        stage_index=stage_index,
                        run_index=len(runs) + 1,
                    )
                )
        return tuple(runs)

    def _build_plan(
        self,
        request: InventorySearchRequest,
        final_state: InventoryState,
        parents: dict[InventoryState, _ParentPointer],
        cost: SearchCost,
        states_explored: int,
    ) -> BatchPlan:
        actions: list[Action] = []
        cursor = final_state
        while cursor in parents:
            parent = parents[cursor]
            actions.append(parent.action)
            cursor = parent.previous_state
        actions.reverse()

        used_macro_kinds = tuple(
            dict.fromkeys(action.macro_kind for action in actions if action.macro_kind)
        )
        used_macro_sources = tuple(
            dict.fromkeys(
                f"{action.macro_kind}:{action.macro_source or 'unknown'}"
                for action in actions
                if action.macro_kind
            )
        )
        runs = self._flatten_actions(actions)
        return BatchPlan(
            target_code=request.target_code,
            target_count=request.target_count,
            sources=dict(request.source_counts),
            steps=runs,
            final_inventory=final_state.to_dict(),
            cost=cost,
            states_explored=states_explored,
            used_macro_kinds=used_macro_kinds,
            used_macro_sources=used_macro_sources,
        )
