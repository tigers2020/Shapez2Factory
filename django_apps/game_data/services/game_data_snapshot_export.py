"""ORM → game_data snapshot payload (EVTC capacity) for the Asteroid Lab CLI core (PR-CLI-2b).

Lives in ``game_data`` so building the snapshot imports only game_data models/services (no cross-app
dependency). The Asteroid Lab side wraps this payload in the core JSON adapter via
``orm_game_data_rules`` and ``manage.py export_game_data_snapshot`` writes it to disk.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.models.mining import MiningExtractionRule
from django_apps.game_data.services.exterior_transport_capacity import (
    space_belt_connector_capacity_per_min_from_row,
    space_pipe_max_per_min_from_row,
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


def _mining_extraction_rule_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in MiningExtractionRule.objects.filter(is_active=True).order_by("resource_kind"):
        rows.append(
            {
                "resource_kind": str(rule.resource_kind),
                "mini_unit_output_per_min": str(rule.mini_unit_output_per_min),
                "output_unit": str(rule.output_unit),
                "max_extension_count": int(rule.max_extension_count),
                "source_kind": str(rule.source_kind),
            }
        )
    return rows


def _dump_hash(*, exterior_rows: list[dict[str, Any]], mining_rows: list[dict[str, Any]]) -> str:
    blob = json.dumps(
        {
            "exterior_transport_capacity": exterior_rows,
            "mining_extraction_rules": mining_rows,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_game_data_snapshot_payload() -> dict[str, Any]:
    """ORM → snapshot payload (resolver output only; capacity formula stays in game_data)."""

    exterior_rows = _exterior_transport_capacity_rows()
    mining_rows = _mining_extraction_rule_rows()
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "game_data_dump_hash": _dump_hash(
            exterior_rows=exterior_rows,
            mining_rows=mining_rows,
        ),
        "exterior_transport_capacity": exterior_rows,
        "mining_extraction_rules": mining_rows,
    }


__all__ = ["SNAPSHOT_SCHEMA_VERSION", "build_game_data_snapshot_payload"]
