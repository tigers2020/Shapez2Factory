"""
Domain types: coordinates, enums, DTOs, and grid conventions.

No I/O, no Django, no v1 solver imports. Algorithm behavior belongs in ``steps``/feature
packages (decode, placement, …), not here.
"""

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox, Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedExistingLayoutContext,
    ExistingLayoutAnalysis,
    Pass1Result,
    Pass2Result,
    RoutingResult,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    SolverTermination,
    SourceKind,
    TransportKind,
)

__all__ = [
    "BBox",
    "Coord",
    "DecodedExistingLayoutContext",
    "ExistingLayoutAnalysis",
    "Pass1Result",
    "Pass2Result",
    "PlacementCommitState",
    "RoutingResult",
    "SolverRunContext",
    "SolverTermination",
    "SourceKind",
    "TransportKind",
]
