"""Compose replay map_view overlay_cells layers (output-only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

_CONNECTOR_ROLE = "planned_exterior_connector"


def _connector_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("overlay_role") or ""),
        int(row["x"]),
        int(row["y"]),
        str(row.get("connector_id") or ""),
    )


def _candidate_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    key: list[object] = [
        str(row.get("overlay_role") or ""),
        str(row.get("kind") or ""),
        int(row["x"]),
        int(row["y"]),
    ]
    if row.get("candidate_id") is not None:
        key.append(str(row["candidate_id"]))
    if row.get("transport") is not None:
        key.append(str(row["transport"]))
    return tuple(key)


def _structural_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("overlay_role") or ""),
        str(row.get("kind") or ""),
        int(row["x"]),
        int(row["y"]),
    )


def _dedupe_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    out: list[dict[str, object]] = []
    for row in rows:
        data = dict(row)
        role = str(data.get("overlay_role") or "")
        if role == _CONNECTOR_ROLE:
            key = _connector_dedupe_key(data)
        elif role:
            key = _structural_dedupe_key(data)
        else:
            key = _candidate_dedupe_key(data)
        if key in seen:
            continue
        seen.add(key)
        out.append(data)
    return out


def _non_connector_structural_rows(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [dict(r) for r in rows if str(r.get("overlay_role") or "") != _CONNECTOR_ROLE]


def compose_replay_overlay_cells(
    *,
    structural_overlay_cells: Sequence[Mapping[str, object]],
    persistent_overlay_cells: Sequence[Mapping[str, object]],
    transient_overlay_cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Merge overlay layers; persistent connector rows must come from plan wire."""

    structural = _non_connector_structural_rows(structural_overlay_cells)
    persistent = [dict(r) for r in persistent_overlay_cells]
    transient = [dict(r) for r in transient_overlay_cells]
    return _dedupe_rows([*structural, *persistent, *transient])


__all__ = ["compose_replay_overlay_cells"]
