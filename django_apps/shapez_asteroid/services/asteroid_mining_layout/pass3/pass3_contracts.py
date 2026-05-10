"""Pass3 transport DTO contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class Pass3TransportResult:
    """Pass3 transport reconstruction result."""

    committed: bool
    transport_cells: dict[Coord, str]
    metrics: dict[str, Any]
