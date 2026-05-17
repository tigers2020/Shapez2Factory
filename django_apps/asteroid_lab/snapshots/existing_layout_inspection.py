"""Existing-layout inspection from A5 decoded top-level cells (read-only; no ORM / replay reads)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
    EquipmentAttachmentDTO,
    ExistingEquipmentDTO,
    ExistingLayoutInspectionDTO,
    ExistingTransportComponentDTO,
)
from django_apps.asteroid_lab.snapshots.server_coords import raw_x_to_dense_x
from django_apps.asteroid_lab.snapshots.transport_components import (
    cell_position_key,
    is_transport_tile,
    iter_four_neighbors,
    sort_key_xy_layer,
)

_EQUIPMENT_KINDS = frozenset(
    {
        "fluid_miner",
        "fluid_miner_extension",
        "shape_miner",
        "shape_miner_extension",
    }
)


def _equipment_id(cell: DecodedCellDTO) -> str:
    layer_s = "null" if cell.layer is None else str(int(cell.layer))
    return f"{cell.x},{cell.y},{layer_s}"


def _overlay_cell(cell: DecodedCellDTO, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "x": cell.x,
        "y": cell.y,
        "layer": cell.layer,
        "rotation": cell.rotation,
        "cell_kind": cell.cell_kind,
        "transport_kind": cell.transport_kind,
        "tile_type": cell.tile_type,
    }
    if cell.server_x is not None and cell.server_y is not None:
        row["server_x"] = cell.server_x
        row["server_y"] = cell.server_y
    row.update(extra)
    return row


def _bbox_of_cells(cells: list[DecodedCellDTO]) -> dict[str, Any]:
    if not cells:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "width": 0, "height": 0}
    xs = [c.x for c in cells]
    ys = [c.y for c in cells]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    out: dict[str, Any] = {
        "min_x": mn_x,
        "max_x": mx_x,
        "min_y": mn_y,
        "max_y": mx_y,
        "width": mx_x - mn_x + 1,
        "height": mx_y - mn_y + 1,
    }
    dense_vals: list[int] = []
    for c in cells:
        if c.x == 0:
            continue
        try:
            dense_vals.append(raw_x_to_dense_x(c.x))
        except ValueError:
            pass
    if dense_vals:
        mndx, mxdx = min(dense_vals), max(dense_vals)
        out["dense_min_x"] = mndx
        out["dense_max_x"] = mxdx
        out["dense_width"] = mxdx - mndx + 1
    if all(c.server_x is not None and c.server_y is not None for c in cells):
        sxs = [int(c.server_x) for c in cells if c.server_x is not None]
        sys_ = [int(c.server_y) for c in cells if c.server_y is not None]
        smn_x, smx_x = min(sxs), max(sxs)
        smn_y, smx_y = min(sys_), max(sys_)
        out["server_min_x"] = smn_x
        out["server_max_x"] = smx_x
        out["server_min_y"] = smn_y
        out["server_max_y"] = smx_y
        out["server_width"] = smx_x - smn_x + 1
        out["server_height"] = smx_y - smn_y + 1
    return out


def _touches_snapshot_bbox(cell: DecodedCellDTO, bbox: dict[str, Any]) -> bool:
    mn_x = int(bbox["min_x"])
    mx_x = int(bbox["max_x"])
    mn_y = int(bbox["min_y"])
    mx_y = int(bbox["max_y"])
    return cell.x == mn_x or cell.x == mx_x or cell.y == mn_y or cell.y == mx_y


def _expected_neighbor_tile_kind(equipment_cell_kind: str) -> str | None:
    if equipment_cell_kind in ("fluid_miner", "fluid_miner_extension"):
        return "space_pipe"
    if equipment_cell_kind in ("shape_miner", "shape_miner_extension"):
        return "space_belt"
    return None


def _index_transport_components(
    cells: tuple[DecodedCellDTO, ...],
    snapshot_bbox: dict[str, Any],
) -> tuple[list[ExistingTransportComponentDTO], dict[tuple[int, int, int | None], int]]:
    """Return transport DTO rows and transport cell → component id map.

    BFS uses raw ``iter_four_neighbors`` (not ``server_x``/``server_y``): rank-dense ``X`` can
    collide for invalid consecutive positives in fixtures. Server coords stay for fingerprint/UI.
    """

    by_key: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        cell_position_key(c): c for c in cells
    }
    next_id = 1
    dtos: list[ExistingTransportComponentDTO] = []
    pos_to_id: dict[tuple[int, int, int | None], int] = {}

    for tk in ("fluid_pipe", "shape_belt"):
        seeds = [c for c in cells if is_transport_tile(c) and c.transport_kind == tk]
        seeds.sort(key=sort_key_xy_layer)
        visited_local: set[tuple[int, int, int | None]] = set()
        for start in seeds:
            sk = cell_position_key(start)
            if sk in visited_local:
                continue
            comp_cells: list[DecodedCellDTO] = []
            stack = [start]
            visited_local.add(sk)
            while stack:
                cur = stack.pop()
                comp_cells.append(cur)
                for nx, ny, nl in iter_four_neighbors(cur.x, cur.y, cur.layer):
                    nk = (nx, ny, nl)
                    nb = by_key.get(nk)
                    if nb is None or not is_transport_tile(nb) or nb.transport_kind != tk:
                        continue
                    if nk in visited_local:
                        continue
                    visited_local.add(nk)
                    stack.append(nb)
            cid = next_id
            next_id += 1
            for cc in comp_cells:
                pos_to_id[cell_position_key(cc)] = cid
            ck = "space_pipe" if tk == "fluid_pipe" else "space_belt"
            touches = any(_touches_snapshot_bbox(c, snapshot_bbox) for c in comp_cells)
            dtos.append(
                ExistingTransportComponentDTO(
                    component_id=cid,
                    transport_kind=tk,
                    cell_kind=ck,
                    cell_count=len(comp_cells),
                    bbox_json=_bbox_of_cells(comp_cells),
                    touches_bbox_edge=touches,
                    cells_json=[
                        _overlay_cell(c, component_id=cid, role="pending") for c in comp_cells
                    ],
                )
            )

    return dtos, pos_to_id


def _pick_main_component_id(
    transport_kind: str,
    components: list[ExistingTransportComponentDTO],
) -> int | None:
    mine = [c for c in components if c.transport_kind == transport_kind]
    if not mine:
        return None
    chosen = min(
        mine,
        key=lambda c: (-c.cell_count, -int(c.touches_bbox_edge), c.component_id),
    )
    return int(chosen.component_id)


def inspect_existing_layout(
    snapshot: DecodedBlueprintSnapshotDTO,
) -> ExistingLayoutInspectionDTO:
    """Pure inspection: top-level cells only; nested ``B.Entries`` stay summarized on cells."""

    bbox = dict(snapshot.bbox_json)
    cells = snapshot.cells
    by_key: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        cell_position_key(c): c for c in cells
    }

    transport_dtos, pos_to_component = _index_transport_components(cells, bbox)
    main_by_kind: dict[str, int | None] = {
        "fluid_pipe": _pick_main_component_id("fluid_pipe", transport_dtos),
        "shape_belt": _pick_main_component_id("shape_belt", transport_dtos),
    }

    role_by_cid: dict[int, str] = {}
    for comp in transport_dtos:
        mk = main_by_kind.get(comp.transport_kind)
        role_by_cid[comp.component_id] = "main" if mk == comp.component_id else "orphan"

    transport_dtos_final: list[ExistingTransportComponentDTO] = []
    for comp in transport_dtos:
        cells_json = [
            {**cell, "role": role_by_cid[comp.component_id], "transport_kind": comp.transport_kind}
            for cell in comp.cells_json
        ]
        transport_dtos_final.append(
            ExistingTransportComponentDTO(
                component_id=comp.component_id,
                transport_kind=comp.transport_kind,
                cell_kind=comp.cell_kind,
                cell_count=comp.cell_count,
                bbox_json=comp.bbox_json,
                touches_bbox_edge=comp.touches_bbox_edge,
                cells_json=cells_json,
            )
        )

    equipment: list[ExistingEquipmentDTO] = []
    for c in cells:
        if c.cell_kind not in _EQUIPMENT_KINDS:
            continue
        equipment.append(
            ExistingEquipmentDTO(
                equipment_id=_equipment_id(c),
                x=c.x,
                y=c.y,
                layer=c.layer,
                rotation=c.rotation,
                tile_type=c.tile_type,
                cell_kind=c.cell_kind,
                transport_kind=c.transport_kind,
                raw_entry_json=dict(c.raw_entry_json),
                server_x=c.server_x,
                server_y=c.server_y,
            )
        )

    attachments: list[EquipmentAttachmentDTO] = []

    for eq in equipment:
        adj_transport: list[dict[str, Any]] = []
        comp_ids: set[int] = set()
        matching_neighbor = False
        main_touch = False

        for nx, ny, nl in iter_four_neighbors(eq.x, eq.y, eq.layer):
            nb = by_key.get((nx, ny, nl))
            if nb is None:
                continue
            if not is_transport_tile(nb):
                continue
            cid = pos_to_component.get((nx, ny, nl))
            extra: dict[str, Any] = {}
            if cid is not None:
                extra["component_id"] = cid
                extra["component_role"] = role_by_cid.get(cid, "unknown")
                comp_ids.add(cid)
            adj_transport.append(_overlay_cell(nb, **extra))

            exp = _expected_neighbor_tile_kind(eq.cell_kind)
            if exp is not None and nb.cell_kind == exp:
                matching_neighbor = True
                tk = nb.transport_kind
                mid = main_by_kind.get(tk)
                if cid is not None and mid is not None and cid == mid:
                    main_touch = True

        sorted_cids = sorted(comp_ids)
        attachments.append(
            EquipmentAttachmentDTO(
                equipment_id=eq.equipment_id,
                adjacent_transport_cells_json=adj_transport,
                adjacent_component_ids=sorted_cids,
                attached_to_any_transport=matching_neighbor,
                attached_to_main_component=main_touch,
            )
        )

    cleanup_cells: list[dict[str, Any]] = []
    for comp in transport_dtos_final:
        if role_by_cid.get(comp.component_id) == "orphan":
            cleanup_cells.extend(comp.cells_json)

    hints_main: dict[str, Any] = {}
    for tk in ("fluid_pipe", "shape_belt"):
        mid = main_by_kind.get(tk)
        if mid is None:
            continue
        main_comp = next((c for c in transport_dtos_final if c.component_id == mid), None)
        if main_comp is None:
            continue
        hints_main[tk] = {
            "component_id": main_comp.component_id,
            "cell_count": main_comp.cell_count,
            "touches_bbox_edge": main_comp.touches_bbox_edge,
            "transport_kind": tk,
            "cell_kind": main_comp.cell_kind,
        }

    hints_json: dict[str, Any] = {
        "main_component_candidate": hints_main,
        "cleanup_candidate_cells": cleanup_cells,
    }

    summary_json: dict[str, Any] = {
        "project_id": snapshot.project_id,
        "map_input_id": snapshot.map_input_id,
        "transport_component_count": len(transport_dtos_final),
        "transport_components_by_kind": {
            "fluid_pipe": sum(1 for c in transport_dtos_final if c.transport_kind == "fluid_pipe"),
            "shape_belt": sum(1 for c in transport_dtos_final if c.transport_kind == "shape_belt"),
        },
        "equipment_count": len(equipment),
        "nested_blueprint_note": (
            "Nested B.Entries remain summarized on each DecodedCellDTO; not unfolded."
        ),
    }

    return ExistingLayoutInspectionDTO(
        project_id=snapshot.project_id,
        map_input_id=snapshot.map_input_id,
        transport_components=tuple(transport_dtos_final),
        equipment=tuple(equipment),
        attachments=tuple(attachments),
        hints_json=hints_json,
        summary_json=summary_json,
    )
