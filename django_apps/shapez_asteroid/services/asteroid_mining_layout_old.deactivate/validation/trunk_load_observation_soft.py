"""Optional diagnostics: STEP4 ``trunk_edge_load`` vs final map transport rows (soft only)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    TRUNK_EDGE_SHARED_THRESHOLD,
)


def trunk_load_observation_soft_warnings(
    mining_map: list[dict[str, Any]],
    trunk_load: Mapping[str, Any] | None,
) -> list[str]:
    """Return human-readable warnings when high-count trunk edges lack matching transport cells.

    Does **not** affect ``geometry_valid`` / ``connectivity_valid``; for debug or CI opt-in only.
    """

    if not isinstance(trunk_load, Mapping):
        return []
    tul = trunk_load.get("transport_usage_load")
    if not isinstance(tul, Mapping):
        return []
    tel = tul.get("trunk_edge_load")
    if not isinstance(tel, Mapping):
        return []
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    for row in mining_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        cells[(x, y)] = row

    warnings: list[str] = []
    for kind, em in tel.items():
        if not isinstance(kind, str) or not isinstance(em, Mapping):
            continue
        wr = want_role(kind)
        for ek, cnt in em.items():
            if not isinstance(ek, str) or not isinstance(cnt, int):
                continue
            if cnt < TRUNK_EDGE_SHARED_THRESHOLD:
                continue
            parts = ek.split("--", 1)
            if len(parts) != 2:
                continue
            try:
                a0, a1 = parts[0].split(",", 1)
                b0, b1 = parts[1].split(",", 1)
                endpoints = ((int(a0), int(a1)), (int(b0), int(b1)))
            except (TypeError, ValueError):
                warnings.append(f"trunk_edge_malformed_key:{kind}:{ek}")
                continue
            for c in endpoints:
                cell_row = cells.get(c)
                if cell_row is None or cell_row.get("role") != wr:
                    warnings.append(f"trunk_edge_endpoint_missing_transport:{kind}:{ek}:{c!r}")
                    break
    return warnings
