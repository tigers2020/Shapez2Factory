"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.copy_json_coords`` (PR-CLI-2f)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.copy_json_coords import (
    COPY_JSON_AXIS_X_RIGHT,
    COPY_JSON_AXIS_Y_DOWN,
    as_entry_int,
    entries_have_explicit_raw_x_zero,
    entry_island_local_xy,
    entry_island_raw_coord,
    entry_raw_r,
    entry_raw_x,
    entry_raw_y,
    iter_entry_dicts,
    raw_x_to_export_column,
)

__all__ = [
    "COPY_JSON_AXIS_X_RIGHT",
    "COPY_JSON_AXIS_Y_DOWN",
    "as_entry_int",
    "entries_have_explicit_raw_x_zero",
    "entry_island_local_xy",
    "entry_island_raw_coord",
    "entry_raw_r",
    "entry_raw_x",
    "entry_raw_y",
    "iter_entry_dicts",
    "raw_x_to_export_column",
]
