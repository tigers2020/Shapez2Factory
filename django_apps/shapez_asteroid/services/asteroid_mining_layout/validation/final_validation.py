"""Final layout validation: geometry + connectivity assertion gate (Stabilization-P0).

Algorithm §15 (STEP9): assertion gate only — this module does **not** create routes, trunks,
or protected-corridor state, does not read or write ``routing_state``, and does not promote
ELA trunk seed or candidate corridors to ``hard_protected_corridors``.

Capacity rated limits are **not** hard failures here; trunk accumulation is trace-only elsewhere.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.mining_map_cell import (
    MiningMapCellsByCoord,
    MiningMapRows,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_to_external,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    blocked_cells,
    layout_kind,
    stub_row_materialized_for_want_role,
    transport_kind_for_extractor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)

_ORPHAN_TRANSPORT_SAMPLE_CAP = 24


__all__ = [
    "FinalValidationReport",
    "count_placement_fsm_rows_on_cells",
    "cells_dict_from_mining_map",
    "external_bbox_margin_for_mining_map",
    "external_margin_from_bbox",
    "external_predicate_for_mining_map",
    "mineable_bbox",
    "orphan_transport_metrics_from_cells",
    "transport_cells_reaching_external",
    "validate_final_mining_layout",
]


def _parse_cells(mining_map: MiningMapRows) -> MiningMapCellsByCoord:
    """Last row wins per coordinate."""

    cells: MiningMapCellsByCoord = {}
    for row in mining_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            continue
        if x == 0:
            continue
        cells[(x, y)] = row
    return cells


def external_margin_from_bbox(width: int, height: int) -> int:
    """mineable bbox 크기에서 동적 external margin을 계산한다 (§3.5 dynamic margin).

    상세: documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md"""
    return max(3, min(7, math.ceil(max(width, height) * 0.15)))


def mineable_bbox(cells: MiningMapCellsByCoord) -> tuple[int, int, int, int] | None:
    """extractor/extension/inferred 셀 기준 validation bbox를 구한다 (§15 hard invariant).

    상세: documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md"""
    mineable: list[Coord] = []
    for c, row in cells.items():
        role = row.get("role")
        lk = layout_kind(row)
        if role == "inferred":
            mineable.append(c)
            continue
        if role != "occupied":
            continue
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            mineable.append(c)
    if not mineable:
        return None
    xs = [p[0] for p in mineable]
    ys = [p[1] for p in mineable]
    return min(xs), max(xs), min(ys), max(ys)


def cells_dict_from_mining_map(mining_map: MiningMapRows) -> MiningMapCellsByCoord:
    """mining_map rows를 좌표 keyed dict로 변환한다 (§15 final validation)."""
    return _parse_cells(mining_map)


def external_predicate_for_mining_map(
    mining_map: MiningMapRows,
) -> Callable[[Coord], bool]:
    """mining_map bbox에서 external predicate를 생성한다 (§3.5 dynamic margin)."""
    cells = _parse_cells(mining_map)
    bbox = mineable_bbox(cells)
    if bbox is None:
        return lambda _: False
    x_min, x_max, y_min, y_max = bbox
    margin = external_margin_from_bbox(x_max - x_min + 1, y_max - y_min + 1)
    return _external_predicate(bbox, margin)


def external_bbox_margin_for_mining_map(
    mining_map: MiningMapRows,
) -> tuple[tuple[int, int, int, int], int] | None:
    """``external_predicate_for_mining_map``과 동일한 mineable bbox·margin 쌍을 반환한다."""

    cells = _parse_cells(mining_map)
    bbox = mineable_bbox(cells)
    if bbox is None:
        return None
    x_min, x_max, y_min, y_max = bbox
    margin = external_margin_from_bbox(x_max - x_min + 1, y_max - y_min + 1)
    return bbox, margin


def _external_predicate(bbox: tuple[int, int, int, int], margin: int) -> Callable[[Coord], bool]:
    """bbox와 margin 밖을 external로 판정하는 predicate를 만든다 (§15 connectivity invariant)."""
    x_min, x_max, y_min, y_max = bbox

    def pred(c: Coord) -> bool:
        """좌표 하나가 external margin 밖인지 판정한다 (§15 connectivity invariant)."""
        x, y = c
        return bool(
            x != 0
            and (
                x < x_min - margin or x > x_max + margin or y < y_min - margin or y > y_max + margin
            )
        )

    return pred


def _neighbor_transport_cells(
    cells: MiningMapCellsByCoord,
    extractor_coord: Coord,
    want_kind: str,
) -> list[Coord]:
    """rotation 정보가 없을 때 인접 belt/pipe stub 후보를 수집한다 (§15 connectivity invariant)."""
    x, y = extractor_coord
    out: list[Coord] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        role = row.get("role")
        if want_kind == "shape_belt" and role == "belt":
            out.append(nxt)
        elif want_kind == "fluid_pipe" and role == "pipe":
            out.append(nxt)
    return out


def _transport_cell_set(cells: MiningMapCellsByCoord) -> set[Coord]:
    """validation 대상 belt/pipe 좌표 집합을 만든다 (§15 hard invariant)."""
    s: set[Coord] = set()
    for c, row in cells.items():
        role = row.get("role")
        if role in ("belt", "pipe"):
            s.add(c)
    return s


def transport_cells_reaching_external(
    transport_cells: set[Coord],
    blocked: set[Coord],
    is_external: Callable[[Coord], bool],
) -> set[Coord]:
    """Transport cells in a component that reaches some cell adjacent to ``is_external`` (BFS)."""

    seeds: list[Coord] = []
    for t in transport_cells:
        x, y = t
        for nxt in neighbors4(x, y):
            if is_external(nxt):
                seeds.append(t)
                break
    q: deque[Coord] = deque(seeds)
    seen: set[Coord] = set(seeds)
    while q:
        cur = q.popleft()
        x, y = cur
        for nxt in neighbors4(x, y):
            if nxt not in transport_cells or nxt in blocked or nxt in seen:
                continue
            seen.add(nxt)
            q.append(nxt)
    return seen


def orphan_transport_metrics_from_cells(
    cells: MiningMapCellsByCoord,
) -> dict[str, Any]:
    """Orphan belt/pipe counts + bounded samples (STEP9-equivalent graph; telemetry only)."""

    transport_cells = _transport_cell_set(cells)
    blocked = blocked_cells(cells)
    bbox = mineable_bbox(cells)

    def never_external(_c: Coord) -> bool:
        return False

    is_external: Callable[[Coord], bool] = never_external
    if bbox is not None:
        x_min, x_max, y_min, y_max = bbox
        w = x_max - x_min + 1
        h = y_max - y_min + 1
        margin = external_margin_from_bbox(w, h)
        is_external = _external_predicate(bbox, margin)

    belt_cells = {c for c in transport_cells if cells.get(c, {}).get("role") == "belt"}
    pipe_cells = {c for c in transport_cells if cells.get(c, {}).get("role") == "pipe"}
    connected_belts = transport_cells_reaching_external(belt_cells, blocked, is_external)
    connected_pipes = transport_cells_reaching_external(pipe_cells, blocked, is_external)
    orphan_belts = belt_cells - connected_belts
    orphan_pipes = pipe_cells - connected_pipes
    otc = len(orphan_belts) + len(orphan_pipes)

    def _samples(coords: set[Coord]) -> list[list[int]]:
        ordered = sorted(coords, key=lambda p: (p[1], p[0]))
        return [[c[0], c[1]] for c in ordered[:_ORPHAN_TRANSPORT_SAMPLE_CAP]]

    return {
        "orphan_transport_count": otc,
        "orphan_fluid_pipe_count": len(orphan_pipes),
        "orphan_shape_belt_count": len(orphan_belts),
        "orphan_pipe_sample_cells": _samples(orphan_pipes),
        "orphan_belt_sample_cells": _samples(orphan_belts),
    }


def _multi_occupied_building_rows_per_cell(mining_map: MiningMapRows) -> int:
    """Count coords with >1 occupied extractor/extension row (duplicate body geometry)."""

    per: dict[Coord, int] = {}
    for row in mining_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            continue
        c = (x, y)
        per[c] = per.get(c, 0) + 1
    return sum(1 for n in per.values() if n > 1)


def _overlap_violations_list(mining_map: MiningMapRows) -> int:
    """Building vs transport overlap + duplicate occupied extractor/extension rows (§15)."""

    by: dict[Coord, set[str]] = {}
    for row in mining_map:
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        lk = layout_kind(row)
        role = row.get("role")
        kind: str | None = None
        if role == "belt" or role == "pipe":
            kind = "transport"
        elif lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            kind = "building"
        if kind is None:
            continue
        by.setdefault((x, y), set()).add(kind)
    transport_body = sum(1 for s in by.values() if "building" in s and "transport" in s)
    return transport_body + _multi_occupied_building_rows_per_cell(mining_map)


def _fixed_output_stub_removed_count(
    mining_map: MiningMapRows,
    cells: MiningMapCellsByCoord,
) -> int:
    """Rows asserting a fixed output stub cell where merged map lacks belt/pipe (§15)."""

    n = 0
    for row in mining_map:
        if (
            row.get("fixed_output_stub") is not True
            and row.get("pass12_fixed_output_stub") is not True
        ):
            continue
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        st = cells.get((x, y))
        if st is None:
            n += 1
            continue
        belt_ok = stub_row_materialized_for_want_role(st, "belt")
        pipe_ok = stub_row_materialized_for_want_role(st, "pipe")
        if not belt_ok and not pipe_ok:
            n += 1
    return n


def count_placement_fsm_rows_on_cells(
    cells: MiningMapCellsByCoord,
) -> tuple[int, int]:
    """Count rows carrying non-terminal placement FSM markers (dedupe keys per row)."""

    quarantined_unrouted_count = 0
    provisional_placed_row_count = 0
    for row in cells.values():
        for key in ("placement_state", "placement_commit_state"):
            ps = row.get(key)
            if not isinstance(ps, str):
                continue
            pl = ps.lower()
            if pl == "quarantined_unrouted":
                quarantined_unrouted_count += 1
                break
            if pl == "provisional_placed":
                provisional_placed_row_count += 1
                break
    return quarantined_unrouted_count, provisional_placed_row_count


def validate_final_mining_layout(mining_map: MiningMapRows) -> FinalValidationReport:
    """최종 mining layout의 geometry/connectivity hard invariant를 검증한다.

        Pass1/Pass2/STEP4/Pass3/Reclaim 이후 반환 직전 gate다 (§15).

    상세: documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md"""
    cells = _parse_cells(mining_map)
    transport_cells = _transport_cell_set(cells)
    blocked = blocked_cells(cells)

    extractor_count = 0
    extension_count = 0
    for row in cells.values():
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            extractor_count += 1
        elif lk in EXTENSIONS:
            extension_count += 1
    transport_cell_count = len(transport_cells)

    overlap_violation_count = _overlap_violations_list(mining_map)

    quarantined_unrouted_count, provisional_placed_row_count = count_placement_fsm_rows_on_cells(
        cells
    )

    bbox = mineable_bbox(cells)
    missing_stub_count = 0
    disconnected_stub_count = 0

    def never_external(_c: Coord) -> bool:
        """bbox가 없을 때 external 도달을 항상 실패 처리하는 fallback predicate다 (§15)."""
        return False

    is_external: Callable[[Coord], bool] = never_external
    if bbox is not None:
        x_min, x_max, y_min, y_max = bbox
        w = x_max - x_min + 1
        h = y_max - y_min + 1
        margin = external_margin_from_bbox(w, h)
        is_external = _external_predicate(bbox, margin)

    fc_transport = frozenset(transport_cells)
    fc_blocked = frozenset(blocked)
    missing_extractor_rotation_count = 0
    for c, row in cells.items():
        lk = layout_kind(row)
        if lk not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            continue
        tk = transport_kind_for_extractor(row)
        if tk is None:
            missing_stub_count += 1
            continue
        raw_r = row.get("r")
        r_known = raw_r if isinstance(raw_r, int) else None
        if r_known is not None:
            stub_cell = shape_miner_output_cell(c, r_known)
            if stub_cell is None:
                missing_stub_count += 1
                continue
            st = cells.get(stub_cell)
            ok_kind = st is not None and (
                (tk == "shape_belt" and stub_row_materialized_for_want_role(st, "belt"))
                or (tk == "fluid_pipe" and stub_row_materialized_for_want_role(st, "pipe"))
            )
            if not ok_kind:
                missing_stub_count += 1
                continue
            if bbox is None or not probe_stub_to_external(
                stub_cell=stub_cell,
                transport_cells=fc_transport,
                blocked_cells=fc_blocked,
                is_external=is_external,
            ):
                disconnected_stub_count += 1
        else:
            missing_extractor_rotation_count += 1
            stubs = _neighbor_transport_cells(cells, c, tk)
            if not stubs:
                missing_stub_count += 1
                continue
            if bbox is None or not any(
                probe_stub_to_external(
                    stub_cell=s,
                    transport_cells=fc_transport,
                    blocked_cells=fc_blocked,
                    is_external=is_external,
                )
                for s in stubs
            ):
                disconnected_stub_count += 1

    belt_cells = {c for c in transport_cells if cells.get(c, {}).get("role") == "belt"}
    pipe_cells = {c for c in transport_cells if cells.get(c, {}).get("role") == "pipe"}
    connected_belts = transport_cells_reaching_external(belt_cells, blocked, is_external)
    connected_pipes = transport_cells_reaching_external(pipe_cells, blocked, is_external)
    orphan_shape_belt_count = len(belt_cells - connected_belts)
    orphan_fluid_pipe_count = len(pipe_cells - connected_pipes)
    orphan_transport_count = orphan_shape_belt_count + orphan_fluid_pipe_count
    transport_connectivity_ok = orphan_transport_count == 0

    fixed_output_stub_removed_count = _fixed_output_stub_removed_count(mining_map, cells)

    geometry_valid = (
        overlap_violation_count == 0
        and quarantined_unrouted_count == 0
        and provisional_placed_row_count == 0
        and missing_stub_count == 0
        and fixed_output_stub_removed_count == 0
    )
    connectivity_valid = disconnected_stub_count == 0 and orphan_transport_count == 0

    return FinalValidationReport(
        geometry_valid=geometry_valid,
        connectivity_valid=connectivity_valid,
        disconnected_stub_count=disconnected_stub_count,
        quarantined_unrouted_count=quarantined_unrouted_count,
        provisional_placed_row_count=provisional_placed_row_count,
        orphan_transport_count=orphan_transport_count,
        overlap_violation_count=overlap_violation_count,
        missing_stub_count=missing_stub_count,
        missing_extractor_rotation_count=missing_extractor_rotation_count,
        extractor_count=extractor_count,
        extension_count=extension_count,
        transport_cell_count=transport_cell_count,
        transport_connectivity_ok=transport_connectivity_ok,
        orphan_shape_belt_count=orphan_shape_belt_count,
        orphan_fluid_pipe_count=orphan_fluid_pipe_count,
        fixed_output_stub_removed_count=fixed_output_stub_removed_count,
    )
