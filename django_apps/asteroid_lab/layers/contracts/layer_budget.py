"""Monotonic time budget owned by stack_runner (L2–L5)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LayerBudgetContext:
    deadline_monotonic: float
    started_monotonic: float
    now_fn: Callable[[], float] = time.monotonic

    @classmethod
    def from_budget_ms(
        cls,
        budget_ms: int,
        *,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> LayerBudgetContext:
        started = now_fn()
        return cls(
            deadline_monotonic=started + budget_ms / 1000,
            started_monotonic=started,
            now_fn=now_fn,
        )

    def remaining_budget_ms(self) -> int:
        return max(0, int((self.deadline_monotonic - self.now_fn()) * 1000))
