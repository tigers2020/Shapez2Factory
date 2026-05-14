"""
STEP 0.5 existing layout analysis (read-only context, §E).

Produces ``ExistingLayoutAnalysis`` without mutating placement. Does not replace
``mineable_placement_cells`` from reconstruction (CANON boundary).
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ExistingLayoutAnalysis,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import SourceKind


def analyze_decoded_layout(_decoded_blueprint: dict[str, Any]) -> ExistingLayoutAnalysis:
    """Build ``ExistingLayoutAnalysis`` from decoded island JSON (not implemented)."""
    msg = "analyze_decoded_layout is not implemented (skeleton only)"
    raise NotImplementedError(msg)


def trivial_unknown_analysis() -> ExistingLayoutAnalysis:
    """Minimal placeholder for tests until decode+analysis exists."""
    return ExistingLayoutAnalysis(
        source_kind=SourceKind.UNKNOWN,
        island_bbox=BBox(min_x=1, min_y=1, max_x=1, max_y=1),
        issues=(),
    )
