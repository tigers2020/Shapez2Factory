"""Aggregate result from stack_runner (L2-L5)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.diagnostic import (
    DiagnosticLayerSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import StackRunStatus


@dataclass(frozen=True, slots=True)
class StackRunResult:
    status: StackRunStatus
    completed_layer_slugs: tuple[str, ...]
    failed_layer_slug: str | None
    diagnostic_snapshot: DiagnosticLayerSnapshot | None
