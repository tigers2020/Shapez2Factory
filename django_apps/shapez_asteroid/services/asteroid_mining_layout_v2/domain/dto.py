"""
Frozen dataclass DTOs (minimal fields for skeleton imports).

Full schemas evolve with CANON ``03_data_schema_dto.md``. No behavior here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    SolverTermination,
    SourceKind,
)


@dataclass(frozen=True, slots=True)
class ReconstructionDTO:
    """STEP 1 outputs (mineable cells, shell, barriers)."""

    mineable_placement_cells: tuple[tuple[int, int], ...] = ()
    extraction_shell_cells: tuple[tuple[int, int], ...] = ()
    full_barrier_cells: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class ExistingLayoutAnalysis:
    """STEP 0.5 read-only summary (§E); fields expanded when analysis is implemented."""

    source_kind: SourceKind
    island_bbox: BBox
    issues: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DecodedExistingLayoutContext:
    """Wrapper for decoded-island analysis (§E.10)."""

    analysis: ExistingLayoutAnalysis


@dataclass(frozen=True, slots=True)
class SolverRunContext:
    """Mutable-by-convention orchestration state; frozen here for skeleton typing only."""

    run_id: str
    reconstruction: ReconstructionDTO
    placement_commit_by_id: dict[str, PlacementCommitState] = field(default_factory=dict)
    termination: SolverTermination | None = None
    decoded_existing_layout: DecodedExistingLayoutContext | None = None


@dataclass(frozen=True, slots=True)
class Pass1Result:
    """STEP 2 Pass1 (§7)."""

    placements: tuple[Any, ...] = ()
    occupied_cells: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class Pass2Result:
    """STEP 3 Pass2 provisional placements (§8)."""

    provisional_placements: tuple[Any, ...] = ()
    blocked_cells_delta: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingResult:
    """STEP 4 routing (§9); trunk_load is aggregate trace only in MVP."""

    routes_by_extractor: dict[str, Any] = field(default_factory=dict)
    trunk_load: dict[str, Any] = field(default_factory=dict)
    routing_failures: tuple[dict[str, Any], ...] = ()
