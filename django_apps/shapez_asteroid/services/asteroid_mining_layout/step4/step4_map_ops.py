"""STEP4 working-map helpers: transport subsets, rollback, row materialization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    transport_cells_reaching_external,
)


def same_kind_transport_cells(cells: dict[Coord, dict[str, Any]], want_role: str) -> set[Coord]:
    """STEP4 trunk 후보가 될 같은 kind belt/pipe 셀을 수집한다 (§9.2)."""
    out: set[Coord] = set()
    for c, row in cells.items():
        if row.get("role") == want_role:
            out.add(c)
    return out


def surface_for_map(cells: dict[Coord, dict[str, Any]]) -> str:
    """새 route row에 찍을 surface 값을 mining_map에서 추론한다 (§9 STEP4 routing)."""
    for row in cells.values():
        s = row.get("surface")
        if s in ("shape", "fluid"):
            return str(s)
    return "shape"


def stub_reaches_external_trunk(
    stub_cell: Coord,
    *,
    cells: dict[Coord, dict[str, Any]],
    want_role: str,
    is_external: Callable[[Coord], bool],
) -> bool:
    """True if stub_cell is same-kind transport in a component that reaches external."""

    blocked_set = _blocked_cells(cells)
    transport_now = same_kind_transport_cells(cells, want_role)
    if stub_cell not in transport_now:
        return False
    trunk = transport_cells_reaching_external(transport_now, set(blocked_set), is_external)
    return stub_cell in trunk


def rollback_placement_cells(
    cells: dict[Coord, dict[str, Any]],
    rec: PlacementCommitRecord,
    final_cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
) -> None:
    """route 실패 placement bundle을 원래 mineable row로 되돌린다 (§9.6 P2-B)."""
    for c in (rec.extractor_cell, *rec.extension_cells, rec.stub_cell):
        if c in mineable and c in final_cells:
            cells[c] = dict(final_cells[c])
        elif c in cells:
            del cells[c]


def stamp_placement_commit_on_map_rows(
    cells: dict[Coord, dict[str, Any]],
    work_records: dict[str, PlacementCommitRecord],
) -> None:
    """Attach FSM metadata to rows with ``placement_id`` (replay / row-level guards, P2-B.1)."""

    for row in cells.values():
        pid = row.get("placement_id")
        if not isinstance(pid, str) or pid not in work_records:
            continue
        rec = work_records[pid]
        row["placement_commit_state"] = rec.state.value
        if rec.route_id is not None:
            row["route_id"] = rec.route_id
        else:
            row.pop("route_id", None)
        if rec.rollback_reason is not None:
            row["rollback_reason"] = rec.rollback_reason
        else:
            row.pop("rollback_reason", None)


def rows_from_cells(cells: dict[Coord, dict[str, Any]]) -> list[dict[str, Any]]:
    """좌표 dict를 replay 가능한 mining_map row 순서로 되돌린다 (§9 STEP4 routing)."""
    ordered = sorted(cells.keys(), key=lambda p: (p[1], p[0]))
    return [dict(cells[k]) for k in ordered]


def baseline_cells_copy(cells: dict[Coord, dict[str, Any]]) -> dict[Coord, dict[str, Any]]:
    return {k: dict(v) for k, v in cells.items()}
