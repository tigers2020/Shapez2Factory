"""STEP4 diagnostics for stub rings fully blocked by ``hard_protected_cells`` (telemetry only)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def _coord_pairs_from_ela_list(raw: Any) -> frozenset[Coord]:
    pairs: set[Coord] = set()
    if not isinstance(raw, list):
        return frozenset()
    for it in raw:
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            try:
                x, y = int(it[0]), int(it[1])
            except (TypeError, ValueError):
                continue
            if x != 0:
                pairs.add((x, y))
    return frozenset(pairs)


def pass12_soft_corridor_cells_from_ela(
    existing_layout_analysis: dict[str, Any] | None,
) -> frozenset[Coord]:
    """Best-effort soft pool from §Pass12 ELA (optional; never affects routing)."""

    if not isinstance(existing_layout_analysis, dict):
        return frozenset()
    raw = existing_layout_analysis.get("pass12_soft_protected_corridor_cells")
    return _coord_pairs_from_ela_list(raw)


def protected_corridor_ids_from_ela(existing_layout_analysis: dict[str, Any] | None) -> list[str]:
    """Return explicit corridor id strings when present on ELA; else empty."""

    if not isinstance(existing_layout_analysis, dict):
        return []
    raw = existing_layout_analysis.get("protected_corridor_ids")
    if isinstance(raw, list):
        out = [str(x) for x in raw if isinstance(x, (str, int))]
        return sorted(dict.fromkeys(out))
    nested = existing_layout_analysis.get("protected_corridors")
    if isinstance(nested, list):
        ids: list[str] = []
        for item in nested:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(str(item["id"]))
        return sorted(dict.fromkeys(ids))
    return []


def build_step4_hard_protected_ring_trace_fields(
    *,
    detail: dict[str, Any],
    stub_cell: Coord,
    trunk_cells: frozenset[Coord],
    hard_extras: frozenset[Coord],
    existing_layout_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    """Per-failure trace for ``hard_protected_ring`` class (all stub neighbors ``hard_protected``).

    Routing is unchanged; this is observation-only for replay / NDJSON audits.
    """

    near = detail.get("blocked_reason_near_stub")
    entries: list[dict[str, Any]] = near if isinstance(near, list) else []

    hard_n = 0
    bypass_n = 0
    soft_n = 0
    soft_extras = pass12_soft_corridor_cells_from_ela(existing_layout_analysis)

    for e in entries:
        if not isinstance(e, dict):
            continue
        reason = str(e.get("reason") or "")
        if reason == "hard_protected":
            hard_n += 1
        elif reason == "ok":
            bypass_n += 1
        elif reason == "blocked":
            cell = e.get("cell")
            if (
                isinstance(cell, (list, tuple))
                and len(cell) >= 2
                and soft_extras
                and (int(cell[0]), int(cell[1])) in soft_extras
            ):
                soft_n += 1

    trunk_beyond = False
    for e in entries:
        if not isinstance(e, dict) or str(e.get("reason") or "") != "hard_protected":
            continue
        cell = e.get("cell")
        if not (isinstance(cell, (list, tuple)) and len(cell) >= 2):
            continue
        try:
            hx, hy = int(cell[0]), int(cell[1])
        except (TypeError, ValueError):
            continue
        if (hx, hy) not in hard_extras:
            # Defensive: ring class expects hard_extras alignment.
            continue
        for v in neighbors4(hx, hy):
            if v == stub_cell:
                continue
            if v in trunk_cells:
                trunk_beyond = True
                break
        if trunk_beyond:
            break

    pc_ids = protected_corridor_ids_from_ela(existing_layout_analysis)

    return {
        "hard_protected_neighbors_near_stub": hard_n,
        "same_kind_trunk_beyond_protected": trunk_beyond,
        "bypass_candidate_count": bypass_n,
        "soft_replace_candidate_count": soft_n,
        "protected_corridor_ids": pc_ids,
    }
