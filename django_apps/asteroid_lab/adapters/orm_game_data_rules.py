"""ORM-backed game-data rules (transitional, Django side) — PR-CLI-2b.

Single semantics path: build the ``game_data_snapshot`` payload from the EVTC ORM (reusing the
game_data resolver functions, never new literals), then answer queries through the core
``JsonSnapshotGameDataRulesAdapter``. The ``export_game_data_snapshot`` command writes the same
payload.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    space_belt_connector_capacity_per_min_from_row,
    space_pipe_max_per_min_from_row,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)

SNAPSHOT_SCHEMA_VERSION = "game_data_snapshot_v1"


def _exterior_transport_capacity_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for shape_row in ExteriorShapeTransportCapacity.objects.filter(is_active=True).order_by(
        "speed_tier"
    ):
        cap = space_belt_connector_capacity_per_min_from_row(shape_row)
        rows.append(
            {
                "resource_kind": "shape",
                "speed_tier": int(shape_row.speed_tier),
                "per_connector_capacity_per_min": str(cap),
            }
        )
    for fluid_row in ExteriorFluidTransportCapacity.objects.filter(is_active=True).order_by(
        "speed_tier"
    ):
        cap = space_pipe_max_per_min_from_row(fluid_row)
        rows.append(
            {
                "resource_kind": "fluid",
                "speed_tier": int(fluid_row.speed_tier),
                "per_connector_capacity_per_min": str(cap),
            }
        )
    return rows


def _dump_hash(rows: list[dict[str, Any]]) -> str:
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_game_data_snapshot_payload() -> dict[str, Any]:
    """ORM → snapshot payload (resolver output only; capacity formula stays in game_data)."""

    rows = _exterior_transport_capacity_rows()
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "game_data_dump_hash": _dump_hash(rows),
        "exterior_transport_capacity": rows,
    }


def build_orm_game_data_rules() -> JsonSnapshotGameDataRulesAdapter:
    """ORM export → core JSON adapter (single resolution path)."""

    return JsonSnapshotGameDataRulesAdapter.from_payload(build_game_data_snapshot_payload())


__all__ = [
    "SNAPSHOT_SCHEMA_VERSION",
    "build_game_data_snapshot_payload",
    "build_orm_game_data_rules",
]
