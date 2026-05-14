"""In-memory trace decision slice (§16.3); validated via ``domain.trace_semantics``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import trace_semantics
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    TransportKind,
)


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """§16.3 trace_event decision slice + identifiers (full replay payload grows elsewhere)."""

    run_id: str
    phase: str
    step_index: int
    event_type: str
    committed: bool
    commit_reason: CommitReason | None
    rejected_reason: RejectedReason | None
    rollback_reason: RollbackReason | None = None
    recovery_trigger: RecoveryTrigger | None = None
    computation_cycle: int | None = None
    route_level: bool = False
    transport_kind: TransportKind | Literal["batch_mixed", "none"] | None = None

    def __post_init__(self) -> None:
        trace_semantics.validate_trace_decision_semantics(
            committed=self.committed,
            commit_reason=self.commit_reason,
            rejected_reason=self.rejected_reason,
            rollback_reason=self.rollback_reason,
        )
        trace_semantics.validate_route_level_trace_transport(
            route_level=self.route_level,
            transport_kind=self.transport_kind,
        )


__all__ = ["TraceEvent"]
