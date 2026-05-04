from __future__ import annotations

from typing import Protocol

from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.search_action import Action
from django_apps.shapez_solver.domain.search_cost import (
    DEFAULT_OPERATION_COST,
    ZERO_SEARCH_COST,
    SearchCost,
)
from django_apps.shapez_solver.services.operation_semantics import apply_operation
from django_apps.shapez_solver.services.pattern_classifier import (
    is_full_source_signature,
    pattern_signature,
)


class MacroRequestView(Protocol):
    @property
    def target_code(self) -> str: ...

    @property
    def target_count(self) -> int: ...

    @property
    def source_counts(self) -> dict[str, int]: ...


class MacroStrategy(Protocol):
    @property
    def code(self) -> str: ...

    @property
    def priority(self) -> int: ...

    def generate(
        self,
        state: InventoryState,
        request: MacroRequestView,
    ) -> tuple[Action, ...]: ...


def _checker_pair_primitive_chain(full_a: str, full_b: str) -> tuple[Action, ...]:
    """서로 다른 full source 두 개에서 ABAB 배치 2개까지 만드는 primitive 체인."""

    left, right = sorted((full_a, full_b))
    o1, o2 = apply_operation(OperationType.SWAPPER, (left, right))
    chain: list[Action] = [
        Action(
            OperationType.SWAPPER,
            (left, right),
            (o1, o2),
            DEFAULT_OPERATION_COST,
        )
    ]
    r1 = apply_operation(OperationType.ROTATE_CW, (o1,))[0]
    r2 = apply_operation(OperationType.ROTATE_CW, (o2,))[0]
    chain.append(Action(OperationType.ROTATE_CW, (o1,), (r1,), DEFAULT_OPERATION_COST))
    chain.append(Action(OperationType.ROTATE_CW, (o2,), (r2,), DEFAULT_OPERATION_COST))
    p1, p2 = sorted((r1, r2))
    x1, x2 = apply_operation(OperationType.SWAPPER, (p1, p2))
    chain.append(Action(OperationType.SWAPPER, (p1, p2), (x1, x2), DEFAULT_OPERATION_COST))
    y1 = apply_operation(OperationType.ROTATE_CW, (x1,))[0]
    chain.append(Action(OperationType.ROTATE_CW, (x1,), (y1,), DEFAULT_OPERATION_COST))
    return tuple(chain)


def _target_tokens(shape_code: str) -> tuple[str, ...]:
    """단일 레이어 shape code를 사분면 토큰으로 나눈다."""

    if ":" in shape_code:
        return ()
    return tuple(shape_code[index : index + 2] for index in range(0, len(shape_code), 2))


def _full_source_code(token: str) -> str:
    """사분면 토큰 하나에 대응하는 full source code를 만든다."""

    return token * 4


def _abcc_source_codes(target_code: str) -> tuple[str, str, str] | None:
    """ABCC 목표에서 A/B/C full source code를 계산한다."""

    tokens = _target_tokens(target_code)
    if len(tokens) != 4:
        return None
    if tokens[2] != tokens[3]:
        return None
    if tokens[0] == tokens[1] or tokens[0] == tokens[2] or tokens[1] == tokens[2]:
        return None
    return (
        _full_source_code(tokens[0]),
        _full_source_code(tokens[1]),
        _full_source_code(tokens[2]),
    )


def _ab_pair_primitive_chain(full_a: str, full_b: str) -> tuple[Action, ...]:
    """A/B full source 한 쌍에서 AB---- 4개를 만든다."""

    chain: list[Action] = []
    out_a, out_b = apply_operation(OperationType.SWAPPER, (full_a, full_b))
    chain.append(
        Action(
            OperationType.SWAPPER,
            (full_a, full_b),
            (out_a, out_b),
            DEFAULT_OPERATION_COST,
        )
    )

    mixed_a = apply_operation(OperationType.ROTATE_CCW, (out_a,))[0]
    chain.append(Action(OperationType.ROTATE_CCW, (out_a,), (mixed_a,), DEFAULT_OPERATION_COST))
    first_target_half, first_leftover = apply_operation(OperationType.CUTTER, (mixed_a,))
    chain.append(
        Action(
            OperationType.CUTTER,
            (mixed_a,),
            (first_target_half, first_leftover),
            DEFAULT_OPERATION_COST,
        )
    )

    mixed_b = apply_operation(OperationType.ROTATE_CW, (out_b,))[0]
    chain.append(Action(OperationType.ROTATE_CW, (out_b,), (mixed_b,), DEFAULT_OPERATION_COST))
    second_target_half, second_leftover = apply_operation(OperationType.CUTTER, (mixed_b,))
    chain.append(
        Action(
            OperationType.CUTTER,
            (mixed_b,),
            (second_target_half, second_leftover),
            DEFAULT_OPERATION_COST,
        )
    )

    for leftover in (first_leftover, second_leftover):
        rotated_leftover = apply_operation(OperationType.ROTATE_CCW, (leftover,))[0]
        chain.append(
            Action(
                OperationType.ROTATE_CCW,
                (leftover,),
                (rotated_leftover,),
                DEFAULT_OPERATION_COST,
            )
        )
        b_single, a_single = apply_operation(OperationType.CUTTER, (rotated_leftover,))
        chain.append(
            Action(
                OperationType.CUTTER,
                (rotated_leftover,),
                (b_single, a_single),
                DEFAULT_OPERATION_COST,
            )
        )
        a_top_left = apply_operation(OperationType.ROTATE_180, (a_single,))[0]
        chain.append(
            Action(
                OperationType.ROTATE_180,
                (a_single,),
                (a_top_left,),
                DEFAULT_OPERATION_COST,
            )
        )
        target_half = apply_operation(OperationType.STACKER, (a_top_left, b_single))[0]
        chain.append(
            Action(
                OperationType.STACKER,
                (a_top_left, b_single),
                (target_half,),
                DEFAULT_OPERATION_COST,
            )
        )

    return tuple(chain)


def _cc_pair_primitive_chain(full_c: str) -> tuple[Action, ...]:
    """C full source 2개에서 ----CC 4개를 만든다."""

    chain: list[Action] = []
    for _ in range(2):
        top_half, bottom_half = apply_operation(OperationType.CUTTER, (full_c,))
        chain.append(
            Action(
                OperationType.CUTTER,
                (full_c,),
                (top_half, bottom_half),
                DEFAULT_OPERATION_COST,
            )
        )
        rotated_top = apply_operation(OperationType.ROTATE_180, (top_half,))[0]
        chain.append(
            Action(
                OperationType.ROTATE_180,
                (top_half,),
                (rotated_top,),
                DEFAULT_OPERATION_COST,
            )
        )
    return tuple(chain)


def _combine_abcc_primitive_chain(target_half: str, bottom_half: str) -> tuple[Action, ...]:
    """AB---- 4개와 ----CC 4개를 ABCC 4개로 합친다."""

    chain: list[Action] = []
    for _ in range(4):
        target = apply_operation(OperationType.STACKER, (target_half, bottom_half))[0]
        chain.append(
            Action(
                OperationType.STACKER,
                (target_half, bottom_half),
                (target,),
                DEFAULT_OPERATION_COST,
            )
        )
    return tuple(chain)


def _abcc_batch_primitive_chain(full_a: str, full_b: str, full_c: str) -> tuple[Action, ...]:
    """ABCC 배치 목표 4개를 만드는 고정 primitive 체인."""

    ab_chain = _ab_pair_primitive_chain(full_a, full_b)
    cc_chain = _cc_pair_primitive_chain(full_c)
    target_half = ab_chain[-1].outputs[0]
    bottom_half = cc_chain[-1].outputs[0]
    return (*ab_chain, *cc_chain, *_combine_abcc_primitive_chain(target_half, bottom_half))


def _wrap_macro_chain(
    chain: tuple[Action, ...],
    *,
    macro_kind: str,
    macro_source: str = "builtin",
) -> Action:
    total_cost: SearchCost = ZERO_SEARCH_COST
    for item in chain:
        total_cost = total_cost + item.cost
    return Action(
        operation=chain[0].operation,
        inputs=chain[0].inputs,
        outputs=chain[-1].outputs,
        cost=total_cost,
        macro_kind=macro_kind,
        macro_source=macro_source,
        primitive_chain=chain,
    )


class CheckerPairMacroStrategy:
    code = "CHECKER_PAIR"
    priority = 10

    def generate(
        self,
        state: InventoryState,
        request: MacroRequestView,
    ) -> tuple[Action, ...]:
        if pattern_signature(request.target_code) != "ABAB":
            return ()
        if state.counts != InventoryState.from_counts(request.source_counts).counts:
            return ()
        if len(state.counts) != 2:
            return ()
        (code_a, count_a), (code_b, count_b) = state.counts
        if count_a != 1 or count_b != 1:
            return ()
        if not is_full_source_signature(code_a) or not is_full_source_signature(code_b):
            return ()
        if code_a == code_b:
            return ()
        if request.target_count != 2:
            return ()
        chain = _checker_pair_primitive_chain(code_a, code_b)
        return (_wrap_macro_chain(chain, macro_kind=self.code),)


class AbccBatchMacroStrategy:
    code = "ABCC_BATCH"
    priority = 20

    def generate(
        self,
        state: InventoryState,
        request: MacroRequestView,
    ) -> tuple[Action, ...]:
        if pattern_signature(request.target_code) != "ABCC":
            return ()
        if request.target_count != 4:
            return ()
        source_codes = _abcc_source_codes(request.target_code)
        if source_codes is None:
            return ()
        full_a, full_b, full_c = source_codes
        expected_sources = {full_a: 1, full_b: 1, full_c: 2}
        if request.source_counts != expected_sources:
            return ()
        if state.counts != InventoryState.from_counts(expected_sources).counts:
            return ()
        if not all(is_full_source_signature(code) for code in source_codes):
            return ()
        chain = _abcc_batch_primitive_chain(full_a, full_b, full_c)
        return (_wrap_macro_chain(chain, macro_kind=self.code),)


DEFAULT_MACRO_STRATEGIES: tuple[MacroStrategy, ...] = tuple(
    sorted(
        (
            CheckerPairMacroStrategy(),
            AbccBatchMacroStrategy(),
        ),
        key=lambda strategy: strategy.priority,
    )
)


__all__ = [
    "AbccBatchMacroStrategy",
    "CheckerPairMacroStrategy",
    "DEFAULT_MACRO_STRATEGIES",
    "MacroRequestView",
    "MacroStrategy",
]
