"""Deterministic signatures for ConnectableSimulation connectable_key."""

from __future__ import annotations

import hashlib
import re

_PIVOT_DIR_RE = re.compile(r";\s*([A-Za-z0-9_]+)\)?\s*$")


def pivot_direction(pivot: object) -> str:
    text = str(pivot or "")
    match = _PIVOT_DIR_RE.search(text)
    if match:
        return match.group(1)
    return text[:32] if text else ""


def connector_type_name(connector: dict[str, object]) -> str:
    raw = connector.get("$type") or ""
    if isinstance(raw, str) and raw:
        return raw.rsplit(".", maxsplit=1)[-1]
    return "connector"


def build_connector_signature(connectors: list[dict[str, object]]) -> str:
    parts: list[str] = []
    for conn in connectors:
        if not isinstance(conn, dict):
            continue
        direction = pivot_direction(conn.get("Pivot"))
        ctype = connector_type_name(conn)
        priority = str(conn.get("UpdatePriority") or "")
        parts.append(f"{direction}:{ctype}:{priority}")
    parts.sort()
    return "|".join(parts)


def simulation_transport_slug(simulation: dict[str, object]) -> str:
    raw = simulation.get("$type") or ""
    if isinstance(raw, str) and raw:
        return raw.rsplit(".", maxsplit=1)[-1]
    return "sim"


def build_lane_signature(
    *,
    simulation: dict[str, object],
    lane_definitions: list[tuple[str, int | None, str]],
) -> str:
    if lane_definitions:
        parts = [
            f"{transport}:{capacity if capacity is not None else '-'}"
            for transport, capacity, _ in lane_definitions
        ]
        parts.sort()
        return "|".join(parts)

    lanes = simulation.get("_Lanes") or simulation.get("InputLanes") or simulation.get("LaneStates")
    if isinstance(lanes, list):
        slug = simulation_transport_slug(simulation)
        return f"{slug}:{len(lanes)}"
    return simulation_transport_slug(simulation)


def build_connectable_key(
    *,
    building_variant_id: int | None,
    num_connectors: int,
    num_occupied_tiles: int,
    connector_signature: str,
    lane_signature: str,
) -> str:
    variant_token = str(building_variant_id) if building_variant_id is not None else "none"
    payload = "|".join(
        [
            variant_token,
            str(num_connectors),
            str(num_occupied_tiles),
            connector_signature,
            lane_signature,
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
