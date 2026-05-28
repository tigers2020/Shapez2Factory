"""Per-layer post-run summary records (observability only; not stack input)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LayerPostSummaryOutcome(StrEnum):
    COMPLETED = "completed"
    SKIPPED_BUDGET = "skipped_budget"


@dataclass(frozen=True, slots=True)
class LayerPostSummaryRecord:
    layer_slug: str
    layer_index: int
    outcome: LayerPostSummaryOutcome
    elapsed_ms: int
    remaining_budget_ms: int | None
    metrics: dict[str, object]
