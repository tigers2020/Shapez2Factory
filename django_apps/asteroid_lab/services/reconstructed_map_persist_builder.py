"""Build layered JSON + ORM entry rows for ``ReconstructedAsteroidMap`` persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    encode_official_copy_string,
    to_game_paste_island_root,
)
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    build_reconstructed_normalized_dto,
    cells_for_field_export,
    cells_for_field_export_from_decoded_json,
)
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.evidence import MINER_EXTENSION_CELL_KINDS
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import _as_int
from django_apps.asteroid_lab.snapshots.server_coords import (
    map_bbox_dense_and_y,
    server_xy_for_raw_xy,
)
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

_MINER_ANCHOR_CELL_KINDS: frozenset[str] = frozenset(
    {
        "fluid_miner",
        "shape_miner",
        "fluid_miner_extension",
        "shape_miner_extension",
    }
)

_EXTRACTOR_TILES: frozenset[str] = frozenset({"Layout_FluidMiner", "Layout_ShapeMiner"})


@dataclass(frozen=True, slots=True)
class ReconstructedMapPersistPayload:
    """ORM-ready payload from reconstruction + cleanup (no replay reads)."""

    decoded_json_lab: dict[str, Any]
    export_json: dict[str, Any]
    reconstruction_json: dict[str, Any]
    rebuilt_copy_code: str
    summary_json: dict[str, Any]
    anchor_raw_x: int | None
    anchor_raw_y: int | None
    anchor_server_x: int | None
    anchor_server_y: int | None
    coord_system: str
    entry_instances: tuple[m.ReconstructedAsteroidEntry, ...] = field(default_factory=tuple)
    cell_count: int = 0
    layout_fingerprint: str = ""


def _cell_kind_to_entry_kind(cell_kind: str) -> str:
    ek = m.ReconstructedAsteroidEntry.EntryKind
    if cell_kind in ("fluid_miner", "shape_miner"):
        return str(ek.MINER)
    if cell_kind in ("fluid_miner_extension", "shape_miner_extension"):
        return str(ek.MINER_EXTENSION)
    if cell_kind == "space_belt":
        return str(ek.BELT)
    if cell_kind == "space_pipe":
        return str(ek.PIPE)
    if cell_kind in ("asteroid_shape_field", "asteroid_fluid_field"):
        return str(ek.ASTEROID_FIELD)
    if cell_kind == "void":
        return str(ek.VOID)
    return str(ek.UNKNOWN)


def _parse_entry_t_fields(t_raw: Any) -> tuple[int | None, str, str]:
    if isinstance(t_raw, int):
        return int(t_raw), "", ""
    if isinstance(t_raw, str):
        return None, t_raw, t_raw
    return None, "", ""


def _coord_system_from_root(root: dict[str, Any]) -> str:
    meta = root.get("_asteroid_lab_coord_system")
    if isinstance(meta, dict):
        cs = meta.get("coord_system")
        if isinstance(cs, str) and cs:
            return cs
    return "server_bbox_left_bottom_dense_x_v1"


def _scan_forbidden_export_keys(obj: Any, *, path: str = "") -> list[str]:
    """Return paths of lab-only keys inside export_json (for tests)."""

    hits: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            sub = f"{path}.{k}" if path else str(k)
            if k in ("server_x", "server_y") or str(k).startswith("_asteroid_lab"):
                hits.append(sub)
            hits.extend(_scan_forbidden_export_keys(v, path=sub))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            hits.extend(_scan_forbidden_export_keys(item, path=f"{path}[{i}]"))
    return hits


def assert_export_json_clean(export_json: dict[str, Any]) -> None:
    hits = _scan_forbidden_export_keys(export_json)
    if hits:
        msg = f"export_json contains lab-only keys: {hits[:5]}"
        raise ValueError(msg)


def _select_anchor(
    *,
    cleanup: CleanupResult | None,
    source_decoded_json: dict[str, Any] | None,
    recon: ReconstructionResult,
) -> tuple[int | None, int | None, int | None, int | None, bool]:
    """Return ``(raw_x, raw_y, server_x, server_y, anchor_fallback)``."""

    params = None
    if cleanup is not None and cleanup.server_xy_params is not None:
        params = cleanup.server_xy_params
    elif recon.server_xy_params is not None:
        params = recon.server_xy_params

    candidates: list[DecodedCellDTO] = []
    if cleanup is not None:
        for c in cleanup.removed_building_cells:
            if c.cell_kind in _MINER_ANCHOR_CELL_KINDS:
                candidates.append(c)

    if candidates:
        pick = min(candidates, key=lambda c: (c.x, c.y))
        sx, sy = pick.server_x, pick.server_y
        if (sx is None or sy is None) and params is not None:
            sx, sy = server_xy_for_raw_xy(
                pick.x, pick.y, min_dense_x=params[0], min_raw_y=params[1]
            )
        return pick.x, pick.y, sx, sy, False

    if source_decoded_json:
        bp = source_decoded_json.get("BP")
        if isinstance(bp, dict):
            entries_raw = bp.get("Entries")
            entries = entries_raw if isinstance(entries_raw, list) else []
            entry_dicts = [e for e in entries if isinstance(e, dict)]
            bbox_params = map_bbox_dense_and_y(entry_dicts)
            extractors: list[tuple[int, int, int | None, int | None]] = []
            for item in entry_dicts:
                t_raw = item.get("T")
                t = str(t_raw) if isinstance(t_raw, str) else ""
                if t in _EXTRACTOR_TILES:
                    x, y = _as_int(item.get("X")), _as_int(item.get("Y"))
                    esx_obj, esy_obj = item.get("server_x"), item.get("server_y")
                    esx: int | None = esx_obj if isinstance(esx_obj, int) else None
                    esy: int | None = esy_obj if isinstance(esy_obj, int) else None
                    if (esx is None or esy is None) and bbox_params is not None:
                        esx, esy = server_xy_for_raw_xy(
                            x, y, min_dense_x=bbox_params[0], min_raw_y=bbox_params[1]
                        )
                    extractors.append((x, y, esx, esy))
            if extractors:
                x, y, sx, sy = min(extractors, key=lambda row: (row[0], row[1]))
                return x, y, sx, sy, False

    if recon.cells:
        with_server = [c for c in recon.cells if c.server_x is not None and c.server_y is not None]
        if with_server:
            pick = min(with_server, key=lambda c: (c.server_x, c.server_y))
            return pick.x, pick.y, pick.server_x, pick.server_y, True

    return None, None, None, None, True


def _reconstruction_cell_row(cell: DecodedCellDTO, *, role: str, source: str) -> dict[str, Any]:
    mineable = cell.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    return {
        "raw_x": cell.x,
        "raw_y": cell.y,
        "server_x": cell.server_x,
        "server_y": cell.server_y,
        "cell_kind": cell.cell_kind,
        "tile_type": cell.tile_type,
        "mineable": mineable,
        "role": role,
        "source": source,
    }


def build_reconstruction_json(
    recon: ReconstructionResult,
    cleanup: CleanupResult | None,
) -> dict[str, Any]:
    cells_out = [
        _reconstruction_cell_row(c, role="reconstructed", source="reconstruction")
        for c in recon.cells
    ]
    removed_out: list[dict[str, Any]] = []
    if cleanup is not None:
        for c in cleanup.removed_building_cells:
            if is_transport_tile(c):
                removed_out.append(
                    _reconstruction_cell_row(c, role="transport_removed", source="cleanup_removed")
                )
            elif c.cell_kind in MINER_EXTENSION_CELL_KINDS or c.cell_kind in (
                "fluid_miner",
                "shape_miner",
            ):
                removed_out.append(
                    _reconstruction_cell_row(c, role="cleanup_evidence", source="cleanup_removed")
                )
            else:
                removed_out.append(
                    _reconstruction_cell_row(c, role="other_removed", source="cleanup_removed")
                )
    return {
        "schema_version": 1,
        "reconstructed_cells": cells_out,
        "cleanup_removed_cells": removed_out,
    }


def _entry_from_bp_row(
    row: dict[str, Any],
    *,
    kind: str,
    source: str,
    bbox_params: tuple[int, int] | None,
) -> m.ReconstructedAsteroidEntry:
    raw_x = _as_int(row.get("X"))
    raw_y = _as_int(row.get("Y"))
    sx_obj, sy_obj = row.get("server_x"), row.get("server_y")
    sx: int | None = sx_obj if isinstance(sx_obj, int) else None
    sy: int | None = sy_obj if isinstance(sy_obj, int) else None
    if (sx is None or sy is None) and bbox_params is not None:
        sx, sy = server_xy_for_raw_xy(
            raw_x, raw_y, min_dense_x=bbox_params[0], min_raw_y=bbox_params[1]
        )
    if sx is None or sy is None:
        msg = "entry row missing server_x/server_y"
        raise ValueError(msg)
    t_num, layout_id, layout_name = _parse_entry_t_fields(row.get("T"))
    rot = row.get("R")
    r_val = _as_int(rot) if rot is not None else None
    return m.ReconstructedAsteroidEntry(
        raw_x=raw_x,
        raw_y=raw_y,
        server_x=int(sx),
        server_y=int(sy),
        t=t_num,
        layout_id=layout_id,
        layout_name=layout_name,
        r=r_val,
        kind=kind,
        source=source,
        payload=dict(row),
    )


def _entry_from_decoded_cell(
    cell: DecodedCellDTO,
    *,
    source: str,
    server_xy_params: tuple[int, int] | None,
) -> m.ReconstructedAsteroidEntry:
    sx, sy = cell.server_x, cell.server_y
    if (sx is None or sy is None) and server_xy_params is not None:
        sx, sy = server_xy_for_raw_xy(
            cell.x, cell.y, min_dense_x=server_xy_params[0], min_raw_y=server_xy_params[1]
        )
    if sx is None or sy is None:
        msg = "cleanup cell missing server coordinates"
        raise ValueError(msg)
    t_num, layout_id, _layout_name = _parse_entry_t_fields(
        cell.tile_type or cell.raw_entry_json.get("T")
    )
    rot = cell.rotation
    payload = (
        dict(cell.raw_entry_json)
        if cell.raw_entry_json
        else {"X": cell.x, "Y": cell.y, "T": cell.tile_type}
    )
    return m.ReconstructedAsteroidEntry(
        raw_x=cell.x,
        raw_y=cell.y,
        server_x=int(sx),
        server_y=int(sy),
        t=t_num,
        layout_id=layout_id,
        layout_name=layout_id,
        r=rot,
        kind=_cell_kind_to_entry_kind(cell.cell_kind),
        source=source,
        payload=payload,
    )


def _dedupe_entry_instances(
    rows: list[m.ReconstructedAsteroidEntry],
) -> tuple[m.ReconstructedAsteroidEntry, ...]:
    """Collapse duplicate ``(server_x, server_y, kind, source)`` (ORM unique constraint)."""

    seen: dict[tuple[int, int, str, str], m.ReconstructedAsteroidEntry] = {}
    for ent in rows:
        key = (int(ent.server_x), int(ent.server_y), str(ent.kind), str(ent.source))
        seen[key] = ent
    return tuple(seen.values())


def build_entry_instances(
    export_json: dict[str, Any],
    recon: ReconstructionResult,
    cleanup: CleanupResult | None,
) -> tuple[m.ReconstructedAsteroidEntry, ...]:
    rows: list[m.ReconstructedAsteroidEntry] = []
    bp = export_json.get("BP")
    entries: list[dict[str, Any]] = []
    if isinstance(bp, dict):
        raw_entries = bp.get("Entries")
        if isinstance(raw_entries, list):
            entries = [e for e in raw_entries if isinstance(e, dict)]
    bbox_params = map_bbox_dense_and_y([{"X": c.x, "Y": c.y} for c in recon.cells]) or (
        cleanup.server_xy_params if cleanup else None
    )

    for item in entries:
        es = m.ReconstructedAsteroidEntry.EntrySource
        rows.append(
            _entry_from_bp_row(
                item,
                kind=str(m.ReconstructedAsteroidEntry.EntryKind.ASTEROID_FIELD),
                source=str(es.RECONSTRUCTION),
                bbox_params=bbox_params,
            )
        )

    if cleanup is not None:
        params = cleanup.server_xy_params
        for cell in cleanup.removed_building_cells:
            rows.append(
                _entry_from_decoded_cell(
                    cell,
                    source=str(m.ReconstructedAsteroidEntry.EntrySource.CLEANUP_REMOVED),
                    server_xy_params=params,
                )
            )
    return _dedupe_entry_instances(rows)


def build_reconstructed_map_persist_payload(
    *,
    map_input_id: int,
    run_key: str,
    recon: ReconstructionResult,
    cleanup: CleanupResult | None = None,
    cleanup_summary: dict[str, Any] | None = None,
    source_decoded_json: dict[str, Any] | None = None,
    layout_fingerprint: str = "",
) -> ReconstructedMapPersistPayload:
    """Assemble all layers from reconstruction/cleanup DTOs (no replay I/O)."""

    merged_summary = {**(cleanup_summary or {}), **dict(recon.summary_json)}
    cells_for_export = cells_for_field_export(tuple(recon.cells))
    if not cells_for_export and source_decoded_json:
        cells_for_export = cells_for_field_export_from_decoded_json(source_decoded_json)
        if cells_for_export:
            merged_summary = {
                **merged_summary,
                "export_fallback": "source_decoded_json",
                "export_fallback_cell_count": len(cells_for_export),
            }

    norm = build_reconstructed_normalized_dto(
        cells_for_export,
        source_decoded_json=source_decoded_json,
        map_input_id=map_input_id,
        run_key=run_key.strip(),
        summary_json=merged_summary,
    )
    decoded_lab = dict(norm.decoded_json)
    export_root = to_game_paste_island_root(decoded_lab)
    assert_export_json_clean(export_root)

    rebuilt = f"{encode_official_copy_string(export_root)}$"
    reconstruction_json = build_reconstruction_json(recon, cleanup)
    arx, ary, asx, asy, anchor_fallback = _select_anchor(
        cleanup=cleanup,
        source_decoded_json=source_decoded_json,
        recon=recon,
    )
    if anchor_fallback:
        merged_summary = {**merged_summary, "anchor_fallback": True}

    coord_system = _coord_system_from_root(decoded_lab)
    entry_rows = build_entry_instances(export_root, recon, cleanup)

    bp = decoded_lab.get("BP")
    entries = bp.get("Entries") if isinstance(bp, dict) else []
    entry_count = len(entries) if isinstance(entries, list) else len(recon.cells)

    return ReconstructedMapPersistPayload(
        decoded_json_lab=decoded_lab,
        export_json=export_root,
        reconstruction_json=reconstruction_json,
        rebuilt_copy_code=rebuilt,
        summary_json=merged_summary,
        anchor_raw_x=arx,
        anchor_raw_y=ary,
        anchor_server_x=asx,
        anchor_server_y=asy,
        coord_system=coord_system,
        entry_instances=entry_rows,
        cell_count=entry_count,
        layout_fingerprint=layout_fingerprint,
    )


__all__ = [
    "ReconstructedMapPersistPayload",
    "assert_export_json_clean",
    "build_entry_instances",
    "build_reconstructed_map_persist_payload",
    "build_reconstruction_json",
    "_dedupe_entry_instances",
    "_scan_forbidden_export_keys",
]
