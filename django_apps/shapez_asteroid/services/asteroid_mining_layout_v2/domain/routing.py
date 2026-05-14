"""STEP 4 routing DTOs (§9) — pure domain; no I/O, Django, preview."""

from __future__ import annotations

from dataclasses import dataclass, field

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    RecoveryTrigger,
    TransportKind,
)


@dataclass(frozen=True, slots=True)
class RoutePath:
    """Ordered route geometry for one logical path."""

    transport_kind: TransportKind
    cells: tuple[BlueprintCell, ...]


@dataclass(frozen=True, slots=True)
class RoutingFailure:
    """§19.1 ``routing_failures`` row (STEP 4)."""

    stub_cell: BlueprintCell
    extractor_id: str | None
    recovery_trigger: RecoveryTrigger | None
    attempt_count: int
    final_state: PlacementCommitState | str | None
    last_error: str | None = None


@dataclass(frozen=True, slots=True)
class TrunkLoadSummary:
    """§3.6 aggregate trace; kind-separated edge maps (keys are implementation-defined)."""

    belt_edge_totals: dict[str, float] = field(default_factory=dict)
    pipe_edge_totals: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Step4RoutingResult:
    """STEP 4 routing (§9); replaces skeleton ``RoutingResult``."""

    routes_by_extractor: dict[str, RoutePath] = field(default_factory=dict)
    trunk_load: TrunkLoadSummary = field(default_factory=TrunkLoadSummary)
    routing_failures: tuple[RoutingFailure, ...] = ()


# Back-compat alias for in-repo skeleton callers (prefer ``Step4RoutingResult``).
RoutingResult = Step4RoutingResult


__all__ = [
    "RoutePath",
    "RoutingFailure",
    "RoutingResult",
    "Step4RoutingResult",
    "TrunkLoadSummary",
]
