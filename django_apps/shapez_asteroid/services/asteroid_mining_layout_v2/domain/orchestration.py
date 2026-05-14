"""§19.1 orchestration snapshot DTOs — pure domain; no I/O, Django, preview, serialization."""

from __future__ import annotations

from dataclasses import dataclass, field

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    SolverTerminationTier,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.existing_layout import (
    DecodedExistingLayoutContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.reconstruction import (
    ReconstructionDTO,
)


@dataclass(frozen=True, slots=True)
class SolverRunLimits:
    max_reclaim_iterations: int = 0
    max_post_reclaim_pass3_reruns: int = 0
    max_total_recovery_attempts: int = 0
    max_validation_recovery_attempts: int = 0
    max_cascade_corrective_attempts: int = 0
    default_reclaim_gain_ratio_threshold: float = 0.0


@dataclass(frozen=True, slots=True)
class RoutingStateSnapshot:
    """§19.1 ``routing_state`` slice (mutable orchestration mirrored as immutable DTO)."""

    trunk_seed_candidates: tuple[BlueprintCell, ...] = ()
    existing_trunk_cells_by_kind: dict[TransportKind, frozenset[BlueprintCell]] = field(
        default_factory=dict
    )
    fixed_output_stub_by_extractor: dict[str, BlueprintCell] = field(default_factory=dict)
    final_route_cells: tuple[BlueprintCell, ...] = ()
    hard_protected_corridors: tuple[BlueprintCell, ...] = ()
    soft_protected_corridors: tuple[BlueprintCell, ...] = ()


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    internal_transport_count: int | None = None
    baseline_internal_transport_at_reclaim_entry: int | None = None
    optimization_baseline_internal_transport: int | None = None


@dataclass(frozen=True, slots=True)
class SolverRunContext:
    """Orchestration snapshot (§19.1)."""

    run_id: str
    reconstruction: ReconstructionDTO
    asteroid_signature: str | None = None
    limits: SolverRunLimits = field(default_factory=SolverRunLimits)
    routing_state: RoutingStateSnapshot = field(default_factory=RoutingStateSnapshot)
    metrics_snapshot: MetricsSnapshot = field(default_factory=MetricsSnapshot)
    placement_commit_by_id: dict[str, PlacementCommitState] = field(default_factory=dict)
    termination: SolverTerminationTier | None = None
    decoded_existing_layout: DecodedExistingLayoutContext | None = None


__all__ = [
    "MetricsSnapshot",
    "RoutingStateSnapshot",
    "SolverRunContext",
    "SolverRunLimits",
]
