"""
Rebuild mining field masks from decoded blueprint (STEP 1, §6).

Must not infer new mineable void during placement passes; reconstruction only here.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)


def reconstruct_asteroid_mining_field(_decoded_blueprint: dict[str, Any]) -> ReconstructionDTO:
    """Populate ``ReconstructionDTO`` from blueprint (not implemented)."""
    msg = "reconstruct_asteroid_mining_field is not implemented (skeleton only)"
    raise NotImplementedError(msg)
