"""Reconstruction pipeline result DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.services.dto import DecodedCellDTO


@dataclass(frozen=True, slots=True)
class ReconstructionResult:
    """Output of :func:`reconstruct_snapshot`."""

    cells: tuple[DecodedCellDTO, ...]
    summary_json: dict[str, Any] = field(default_factory=dict)
    outer_rim_coords: tuple[tuple[int, int], ...] = ()
