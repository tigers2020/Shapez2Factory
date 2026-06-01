"""``GameDataRulesPort`` ??solver-facing game-data rules (L2 decouple, PR-CLI-2b).

The core satisfies this port via a frozen ``game_data_snapshot.json`` (see
``JsonSnapshotGameDataRulesAdapter``); the Django side produces the same snapshot from the ORM via a
single export path. ``ExteriorCapacityRow`` is re-exported here for callers that imported it from
the PR-CLI-1 placeholder location.
"""

from __future__ import annotations

from typing import Protocol

from shapez2_factory.domain.asteroid_lab.exterior_capacity_row import ExteriorCapacityRow
from shapez2_factory.domain.asteroid_lab.mining_extraction_row import MiningExtractionRow


class GameDataRulesPort(Protocol):
    def exterior_connector_capacity(
        self,
        *,
        resource_kind: str,
        speed_tier: int,
    ) -> ExteriorCapacityRow:
        """Return the per-connector capacity row; raise ``LookupError`` when no row exists."""
        ...

    def mining_extraction_rule(self, *, resource_kind: str) -> MiningExtractionRow:
        """Return the active mining extraction row; raise ``LookupError`` when no row exists."""
        ...


__all__ = ["ExteriorCapacityRow", "GameDataRulesPort", "MiningExtractionRow"]
