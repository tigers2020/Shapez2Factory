"""ORM-backed game-data rules (transitional, Django side) — PR-CLI-2b.

Single semantics path: the game_data snapshot payload is built by
``game_data.services.game_data_snapshot_export`` (game_data-only deps), then answered through the
core ``JsonSnapshotGameDataRulesAdapter``. This is the sole sanctioned asteroid_lab→game_data ORM
bridge (see import-matrix skip list).
"""

from __future__ import annotations

from django_apps.game_data.services.game_data_snapshot_export import (
    SNAPSHOT_SCHEMA_VERSION,
    build_game_data_snapshot_payload,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)


def build_orm_game_data_rules() -> JsonSnapshotGameDataRulesAdapter:
    """ORM export → core JSON adapter (single resolution path)."""

    return JsonSnapshotGameDataRulesAdapter.from_payload(build_game_data_snapshot_payload())


__all__ = [
    "SNAPSHOT_SCHEMA_VERSION",
    "build_game_data_snapshot_payload",
    "build_orm_game_data_rules",
]
