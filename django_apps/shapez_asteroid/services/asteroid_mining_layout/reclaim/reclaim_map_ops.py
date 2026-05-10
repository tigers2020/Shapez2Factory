"""P4 reclaim: mining_map snapshots, provisional rows, transport/mineable helpers."""

from __future__ import annotations

import copy
import math
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO,
    MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS,
    P4_RECLAIM_PROVISIONAL_PLACEMENT_ID,
    P4_REJECT_FINAL_ROUTE_OVERLAP,
    P4_REJECT_HARD_PROTECTED_CORRIDOR,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_REJECT_VALIDATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    rotation_r_for_extension_facing_parent,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind as _layout_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)


def _mining_map_snapshot(mining_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reclaim loop rollback용 mining_map row snapshot을 만든다 (§12.2 budget)."""
    return copy.deepcopy(mining_map)


def _rebuild_mining_map_from_cells(cells: dict[Coord, dict[str, Any]]) -> list[dict[str, Any]]:
    """좌표 dict에서 Reclaim loop mining_map rows를 재구성한다 (§12.2)."""
    ordered = sorted(cells.keys(), key=lambda p: (p[1], p[0]))
    return [dict(cells[k]) for k in ordered]


def _provisional_reclaim_layout_rows(
    *,
    anchor: Coord,
    extension: Coord,
    rotation: int,
    transport_kind: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Coord]:
    """P4 후보 적용 후 provisional layout rows를 만든다 (§12.2 budget)."""
    stub = shape_miner_output_cell(anchor, rotation)
    if stub is None:
        raise ValueError("stub required for provisional reclaim rows")
    if transport_kind == "shape_belt":
        surface = "shape"
        miner_layout = "miner"
        miner_t = "Layout_ShapeMiner"
        ext_layout = "extension"
        ext_t = "Layout_ShapeMinerExtension"
        transport_role = "belt"
    elif transport_kind == "fluid_pipe":
        surface = "fluid"
        miner_layout = "fluid_miner"
        miner_t = "Layout_FluidMiner"
        ext_layout = "fluid_extension"
        ext_t = "Layout_FluidMinerExtension"
        transport_role = "pipe"
    else:
        raise ValueError(f"unknown transport_kind {transport_kind!r}")
    edx, edy = anchor[0] - extension[0], anchor[1] - extension[1]
    ext_r = rotation_r_for_extension_facing_parent((edx, edy))
    miner_row: dict[str, Any] = {
        "x": anchor[0],
        "y": anchor[1],
        "role": "occupied",
        "surface": surface,
        "layout_kind": miner_layout,
        "t": miner_t,
        "r": rotation,
        "placement_id": P4_RECLAIM_PROVISIONAL_PLACEMENT_ID,
    }
    ext_row: dict[str, Any] = {
        "x": extension[0],
        "y": extension[1],
        "role": "occupied",
        "surface": surface,
        "layout_kind": ext_layout,
        "t": ext_t,
        "r": ext_r,
        "placement_id": P4_RECLAIM_PROVISIONAL_PLACEMENT_ID,
    }
    stub_row: dict[str, Any] = {
        "x": stub[0],
        "y": stub[1],
        "role": transport_role,
        "surface": surface,
        "placement_id": P4_RECLAIM_PROVISIONAL_PLACEMENT_ID,
    }
    return miner_row, ext_row, stub_row, stub


def _p4_overlap_reject_reason(
    placed: frozenset[Coord],
    *,
    final_route_cells: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    soft_protected_corridors: frozenset[Coord],
    committed_building_cells: frozenset[Coord],
) -> str | None:
    """P4 후보가 protected corridor 또는 body와 충돌하는 이유를 판정한다 (§12.2)."""
    if placed & final_route_cells:
        return P4_REJECT_FINAL_ROUTE_OVERLAP
    if placed & hard_protected_corridors:
        return P4_REJECT_HARD_PROTECTED_CORRIDOR
    if placed & soft_protected_corridors:
        return P4_REJECT_SOFT_PROTECTED_CORRIDOR
    if placed & committed_building_cells:
        return P4_REJECT_VALIDATION
    return None


def _interior_transport_cells(
    mining_map: list[dict[str, Any]],
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
) -> frozenset[Coord]:
    """현재 map에서 asteroid interior transport 셀을 수집한다 (§12 Reclaim loop)."""
    cells = cells_dict_from_mining_map(mining_map)
    out: set[Coord] = set()
    for c, row in cells.items():
        if row.get("role") not in ("belt", "pipe"):
            continue
        if c in mineable and c in asteroid:
            out.add(c)
    return frozenset(out)


def _all_transport_cells(mining_map: list[dict[str, Any]]) -> frozenset[Coord]:
    """현재 map의 모든 belt/pipe transport 셀을 수집한다 (§12 Reclaim loop)."""
    cells = cells_dict_from_mining_map(mining_map)
    return frozenset(c for c, row in cells.items() if row.get("role") in ("belt", "pipe"))


def _committed_building_cells(mining_map: list[dict[str, Any]]) -> frozenset[Coord]:
    """Occupied cells that hold extractors, extensions, or other non-field buildings."""

    cells = cells_dict_from_mining_map(mining_map)
    out: set[Coord] = set()
    for c, row in cells.items():
        if row.get("role") != "occupied":
            continue
        lk = _layout_kind(row)
        if lk is None or lk == "asteroid_field":
            continue
        out.add(c)
    return frozenset(out)


def _reclaimed_interior_transport_cells(
    map_before_pass3: list[dict[str, Any]],
    map_after_pass3: list[dict[str, Any]],
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
) -> frozenset[Coord]:
    """baseline 대비 회수된 interior transport 셀을 계산한다 (§12.2 gain_ratio)."""
    before = _interior_transport_cells(map_before_pass3, mineable=mineable, asteroid=asteroid)
    after = _interior_transport_cells(map_after_pass3, mineable=mineable, asteroid=asteroid)
    return frozenset(before - after)


def _mineable_cur_for_reclaim(
    mineable_base: frozenset[Coord],
    *,
    final_route_cells: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    soft_protected_corridors: frozenset[Coord],
    committed_building_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """Reclaim 평가에 사용할 현재 mineable 후보 셀을 수집한다 (§12.2)."""
    return frozenset(
        mineable_base
        - final_route_cells
        - hard_protected_corridors
        - soft_protected_corridors
        - committed_building_cells
    )


def _allowed_internal_transport_budget(pass3_internal_transport_saved: int) -> int:
    """Reclaim loop의 internal_transport_budget 상한을 계산한다 (§12.2 budget)."""
    saved = max(0, pass3_internal_transport_saved)
    base_spend = math.floor(saved * MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO)
    if saved > 0:
        return max(0, base_spend)
    return MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS


def _transport_role_dict_from_map(mining_map: list[dict[str, Any]]) -> dict[Coord, str]:
    """현재 map의 transport role을 좌표 dict로 만든다 (§12.2)."""
    cells = cells_dict_from_mining_map(mining_map)
    out: dict[Coord, str] = {}
    for c, row in cells.items():
        role = row.get("role")
        if role == "belt":
            out[c] = "belt"
        elif role == "pipe":
            out[c] = "pipe"
    return out
