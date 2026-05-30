"""``GameDataRulesPort`` — solver-facing game-data rules (L2 decouple).

The full ``ExteriorCapacityRow`` and the JSON-snapshot adapter land in PR-CLI-2b; the row below is a
minimal placeholder so the port type-checks while the use case is still a stub.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExteriorCapacityRow:
    """Placeholder capacity row; full field set finalized in PR-CLI-2b."""

    speed_tier: int
    shapes_per_minute: float


class GameDataRulesPort(Protocol):
    def exterior_shape_capacity(self, *, speed_tier: int) -> ExteriorCapacityRow: ...


__all__ = ["ExteriorCapacityRow", "GameDataRulesPort"]
