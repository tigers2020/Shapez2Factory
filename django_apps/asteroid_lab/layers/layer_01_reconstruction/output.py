"""Layer 1 output DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap


@dataclass(frozen=True, slots=True)
class Layer01ReconstructionOutput:
    complete_map: ReconstructionCompleteMap
    capacity_envelope: dict[str, Any]
