"""Deterministic SHA-256 digest for mining layout solver state (map + routing subset)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    ROUTING_STATE_KEYS_STEP4_HASH,
)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _normalize_mining_map_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort rows by (y, x); each row dict has keys sorted for stable JSON."""

    norm: list[tuple[tuple[int, int], dict[str, Any]]] = []
    for raw in rows:
        row = dict(raw)
        x = int(row.get("x", 0))
        y = int(row.get("y", 0))
        stable = {k: row[k] for k in sorted(row)}
        norm.append(((y, x), stable))
    norm.sort(key=lambda t: t[0])
    return [t[1] for t in norm]


def _normalize_coord_pairs(val: object) -> list[list[int]]:
    if not isinstance(val, list):
        return []
    pairs: list[tuple[int, int, list[int]]] = []
    for item in val:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            a, b = item[0], item[1]
            try:
                xi, yi = int(a), int(b)
            except (TypeError, ValueError):
                continue
            pairs.append((xi, yi, [xi, yi]))
    pairs.sort(key=lambda t: (t[1], t[0]))
    return [t[2] for t in pairs]


def routing_state_subset_for_hash(
    rs: Mapping[str, Any] | None,
    *,
    keys: tuple[str, ...] = ROUTING_STATE_KEYS_STEP4_HASH,
) -> dict[str, Any] | None:
    """Stable routing JSON for hashing (default: hard/soft protected corridor lists)."""

    if not isinstance(rs, Mapping):
        return None
    out: dict[str, Any] = {}
    for key in keys:
        if key in rs:
            out[key] = _normalize_coord_pairs(rs[key])
    return out or None


def normalized_solver_state_payload(
    mining_map: list[dict[str, Any]],
    *,
    routing_state: Mapping[str, Any] | None = None,
    routing_state_keys: tuple[str, ...] | None = ROUTING_STATE_KEYS_STEP4_HASH,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "mining_map": _normalize_mining_map_rows(mining_map),
    }
    if routing_state_keys is not None and routing_state is not None:
        rsub = routing_state_subset_for_hash(routing_state, keys=routing_state_keys)
        if rsub is not None:
            payload["routing_state"] = rsub
    return payload


def solver_state_sha256_hex(
    mining_map: list[dict[str, Any]],
    *,
    routing_state: Mapping[str, Any] | None = None,
    routing_state_keys: tuple[str, ...] | None = ROUTING_STATE_KEYS_STEP4_HASH,
) -> str:
    """SHA-256 hex; ``routing_state_keys=None`` omits routing (map-only)."""

    raw = _json_bytes(
        normalized_solver_state_payload(
            mining_map,
            routing_state=routing_state,
            routing_state_keys=routing_state_keys,
        )
    )
    return hashlib.sha256(raw).hexdigest()


def solver_state_hash_hex(
    mining_map: list[dict[str, Any]],
    *,
    routing_state: Mapping[str, Any] | None = None,
) -> str:
    """Convenience alias: map + default corridor routing subset when ``routing_state`` set."""

    return solver_state_sha256_hex(mining_map, routing_state=routing_state)


def mining_map_state_hash(mining_map: list[dict[str, Any]]) -> str:
    """Map-only digest."""

    return solver_state_sha256_hex(mining_map, routing_state=None, routing_state_keys=None)


def normalized_mining_map(mining_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Public alias for row-normalized map (tests, replay diff)."""

    return _normalize_mining_map_rows(mining_map)


__all__ = [
    "ROUTING_STATE_KEYS_STEP4_HASH",
    "mining_map_state_hash",
    "normalized_mining_map",
    "normalized_solver_state_payload",
    "routing_state_subset_for_hash",
    "solver_state_hash_hex",
    "solver_state_sha256_hex",
]
