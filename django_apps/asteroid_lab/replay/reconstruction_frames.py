"""Replay helpers: topology reconstruction rows and stepwise snapshot events."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.trace import (
    ReconstructionTraceCollector,
    ReconstructionTraceEvent,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_RECONSTRUCTION_BEGIN,
    EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL,
    EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED,
    EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED,
    EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED,
    EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    cell_key_xy_layer,
    decoded_cell_to_full_map_row,
    diff_maps,
    rows_from_cells,
    snapshot_summary_from_rows,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO, SnapshotEventDTO

__all__ = [
    "ReconstructionTraceCollector",
    "build_reconstruction_replay_events",
]


def _sort_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: cell_key_xy_layer(r))


def _trace_marker_row(x: int, y: int, layer: int | None) -> dict[str, Any]:
    return {
        "x": x,
        "y": y,
        "layer": layer,
        "rotation": 0,
        "cell_kind": "internal_void",
        "transport_kind": "none",
        "tile_type": "",
        "_replay_trace": True,
    }


def _snapshot_event_type_for_trace(tt: str) -> str:
    if tt in ("wall_projection", "reconstruction_skip"):
        return EVENT_TYPE_RECONSTRUCTION_BEGIN
    if tt in (
        "shell_row_span",
        "shell_col_span",
        "inferred_shell_complete",
        "barrier_build",
    ):
        return EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED
    if tt in ("flood_seed", "flood_batch", "flood_complete"):
        return EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL
    if tt in ("interior_candidates", "component_detected"):
        return EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED
    if tt == "component_guard":
        return EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED
    if tt in ("fill_commit", "reconstruction_final"):
        return EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED
    return EVENT_TYPE_RECONSTRUCTION_BEGIN


def _title_for_trace(tt: str) -> str:
    return tt.replace("_", " ").title()


def build_reconstruction_replay_events(
    *,
    structural_rows: list[dict[str, Any]],
    cleanup: CleanupResult,
    recon: ReconstructionResult,
    trace_events: Sequence[ReconstructionTraceEvent],
    recon_summary: dict[str, Any],
    hints: dict[str, Any],
    final_issue_cells: list[dict[str, Any]] | None = None,
) -> list[SnapshotEventDTO]:
    """Convert trace events into persisted replay frames (full_map + diff per step)."""

    default_layer: int | None = cleanup.cleaned_cells[0].layer if cleanup.cleaned_cells else None
    merged: dict[tuple[int, int, int | None], dict[str, Any]] = {}
    for r in structural_rows:
        if not isinstance(r, dict):
            continue
        try:
            merged[cell_key_xy_layer(r)] = dict(r)
        except (KeyError, TypeError, ValueError):
            continue

    final_rows = rows_from_cells(recon.cells)
    recon_by_key: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        (c.x, c.y, c.layer): c for c in recon.cells
    }
    prev_display = _sort_rows(list(merged.values()))
    out: list[SnapshotEventDTO] = []

    marker_trace_types = frozenset(
        {
            "wall_projection",
            "shell_row_span",
            "shell_col_span",
            "inferred_shell_complete",
            "barrier_build",
            "flood_seed",
            "flood_batch",
            "flood_complete",
            "interior_candidates",
            "component_detected",
            "component_guard",
        }
    )

    for ev in trace_events:
        tt = ev.trace_event_type
        ek = str(ev.summary_json.get("event_key") or f"step4_trace_{tt}")
        event_type = _snapshot_event_type_for_trace(tt)
        next_merged = dict(merged)

        if tt == "fill_commit":
            for x, y in ev.coords:
                key3 = (x, y, default_layer)
                cell = recon_by_key.get(key3)
                if cell is None:
                    kind = str(ev.summary_json.get("cell_kind") or "asteroid_shape_field")
                    cell = DecodedCellDTO(
                        x=x,
                        y=y,
                        layer=default_layer,
                        rotation=0,
                        tile_type="",
                        cell_kind=kind,
                        transport_kind="none",
                        has_nested_blueprint=False,
                        nested_entry_count=0,
                        nested_type_counts_json={},
                        raw_entry_json={
                            "_replay_synthetic": True,
                            "_reconstruction": "topology_fill",
                        },
                        server_x=None,
                        server_y=None,
                    )
                next_merged[key3] = decoded_cell_to_full_map_row(cell)

        if tt == "reconstruction_final":
            next_merged = {cell_key_xy_layer(r): dict(r) for r in final_rows}

        next_display = _sort_rows(list(next_merged.values()))
        if tt in marker_trace_types:
            markers = [_trace_marker_row(x, y, default_layer) for x, y in sorted(ev.coords)]
            empty_diff = diff_maps(prev_display, prev_display)
            diff_payload: dict[str, Any] = {
                "added": markers,
                "removed": list(empty_diff.get("removed") or []),
                "changed": list(empty_diff.get("changed") or []),
            }
        elif tt == "fill_commit":
            diff_payload = diff_maps(prev_display, next_display)
        else:
            diff_payload = diff_maps(prev_display, next_display)

        summary_row = snapshot_summary_from_rows(next_display)
        if tt == "reconstruction_final":
            summary_out: dict[str, Any] = {**dict(recon_summary), **dict(summary_row)}
        else:
            summary_out = dict(summary_row)

        trace_meta = {k: v for k, v in ev.summary_json.items() if k != "event_key"}
        metrics: dict[str, Any] = {
            **dict(recon_summary),
            **dict(summary_row),
            "trace_event_type": tt,
            **trace_meta,
        }

        overlay: dict[str, Any] = {"cells": next_display}
        dto = SnapshotEventDTO(
            event_key=ek,
            phase="reconstruction",
            phase_step=tt,
            event_type=event_type,
            title=_title_for_trace(tt),
            description=f"Reconstruction trace: {tt}",
            after_state_json={"hints_json": hints},
            cell_overlay_json=overlay,
            metrics_json=metrics,
            is_decision_point=(tt == "reconstruction_final"),
            full_map=list(next_display),
            diff=diff_payload,
            summary=summary_out,
        )
        out.append(dto)
        prev_display = next_display
        merged = next_merged

    if out and final_issue_cells is not None:
        last = out[-1]
        out[-1] = replace(
            last,
            cell_overlay_json={
                **last.cell_overlay_json,
                "issue_cells": list(final_issue_cells),
            },
        )
    return out
