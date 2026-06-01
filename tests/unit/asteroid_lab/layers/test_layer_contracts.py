"""Contracts for layer stack budget and status."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus


def test_stack_run_status_values() -> None:
    assert StackRunStatus.SUCCESS.value == "success"
    assert StackRunStatus.TIMEOUT_FAIL_CLOSED.value == "timeout_fail_closed"


def test_layer_budget_context_remaining_ms() -> None:
    ctx = LayerBudgetContext(
        deadline_monotonic=1000.0,
        started_monotonic=940.0,
        now_fn=lambda: 940.0,
    )
    assert ctx.remaining_budget_ms() == 60_000


def test_layer_budget_context_exhausted_returns_zero() -> None:
    ctx = LayerBudgetContext(
        deadline_monotonic=1000.0,
        started_monotonic=940.0,
        now_fn=lambda: 1001.0,
    )
    assert ctx.remaining_budget_ms() == 0


def test_layer_budget_context_from_budget_ms() -> None:
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 100.0)
    assert ctx.started_monotonic == 100.0
    assert ctx.deadline_monotonic == 160.0
    assert ctx.remaining_budget_ms() == 60_000
