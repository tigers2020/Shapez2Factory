"""Layer 1 output DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


@dataclass(frozen=True, slots=True)
class Layer01ReconstructionOutput:
    complete_map: ReconstructionCompleteMap
    capacity_envelope: dict[str, Any]
