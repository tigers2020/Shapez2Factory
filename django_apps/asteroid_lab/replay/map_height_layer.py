"""Shapez 2 island height layer (L=0/1/2) for replay wire cells.

Golden map copy strings use three stacked planes (floor / fluid / void transport).
Replay UI filters on ``layer``; explicit decode values win, otherwise infer from
cell_kind + transport_kind + tile_type.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_REPLAY_HEIGHT_LAYER_MIN = 0
_REPLAY_HEIGHT_LAYER_MAX = 2

_SHAPE_FIELD_KINDS = frozenset(
    {
        "asteroid_shape_field",
        "shape_miner",
        "shape_miner_extension",
        "inner_field_block",
    }
)
_FLUID_FIELD_KINDS = frozenset(
    {
        "asteroid_fluid_field",
        "fluid_miner",
        "fluid_miner_extension",
    }
)
_VOID_TRANSPORT_KINDS = frozenset(
    {
        "space_belt",
        "shape_belt",
        "route_probe_path",
        "route_path",
        "route_probe",
        "route_goal",
        "confirmed_route",
        "candidate_route_path",
        "overlap_conflict",
    }
)
_FLUID_TRANSPORT_KINDS = frozenset(
    {
        "space_pipe",
        "fluid_pipe",
    }
)

_FLUID_TRANSPORT_VALUES = frozenset({"fluid", "fluid_pipe"})
_SHAPE_TRANSPORT_VALUES = frozenset({"shape", "shape_belt"})


def wire_coord_int(value: object) -> int:
    """Coerce replay wire coordinates for dedupe keys (invalid → 0)."""

    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    return 0


def clamp_replay_height_layer(value: object) -> int:
    if isinstance(value, bool):
        return _REPLAY_HEIGHT_LAYER_MIN
    if isinstance(value, int):
        n = value
    elif isinstance(value, (float, str)):
        try:
            n = int(value)
        except (ValueError, TypeError):
            return _REPLAY_HEIGHT_LAYER_MIN
    else:
        return _REPLAY_HEIGHT_LAYER_MIN
    return max(_REPLAY_HEIGHT_LAYER_MIN, min(_REPLAY_HEIGHT_LAYER_MAX, n))


def wire_explicit_height_layer(data: Mapping[str, Any]) -> int | None:
    for key in ("layer", "L", "z", "Z"):
        if key not in data:
            continue
        raw = data[key]
        if raw is None or raw == "":
            continue
        return clamp_replay_height_layer(raw)
    return None


def resolve_replay_height_layer(
    *,
    cell_kind: str = "",
    transport_kind: str = "",
    tile_type: str = "",
    layer: int | None = None,
) -> int:
    if layer is not None:
        return clamp_replay_height_layer(layer)

    kind = str(cell_kind or "")
    transport = str(transport_kind or "")
    tile = str(tile_type or "")

    if kind == "candidate_miner":
        if transport in _FLUID_TRANSPORT_VALUES:
            return 1
        return 0

    if kind == "candidate_transport_stub":
        if transport in _FLUID_TRANSPORT_VALUES:
            return 1
        return 2

    if kind in _VOID_TRANSPORT_KINDS:
        if transport in _FLUID_TRANSPORT_VALUES and kind not in {"space_belt", "shape_belt"}:
            return 1
        return 2

    if kind in _FLUID_TRANSPORT_KINDS:
        return 1

    if kind in _FLUID_FIELD_KINDS or transport in _FLUID_TRANSPORT_VALUES:
        return 1

    if kind in _SHAPE_FIELD_KINDS or transport in _SHAPE_TRANSPORT_VALUES:
        return 0

    if "route" in kind:
        if transport in _FLUID_TRANSPORT_VALUES:
            return 1
        return 2

    if "SpacePipe" in tile or tile.startswith("SpacePipe"):
        return 1
    if "SpaceBelt" in tile or tile.startswith("SpaceBelt"):
        return 2
    if "Lift2" in tile:
        return 2
    if "Lift1" in tile:
        return 1

    return 0


def wire_transport_kind_for_layer_resolution(row: Mapping[str, Any]) -> str:
    kind = str(row.get("kind") or row.get("cell_kind") or "")
    if kind in {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
        "route_probe_path",
        "inner_field_block",
    }:
        output_transport = row.get("output_transport_kind")
        if output_transport is not None and str(output_transport).strip():
            return str(output_transport)
    return str(row.get("transport_kind") or row.get("transport") or "")


def enrich_replay_wire_row_with_layer(row: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    explicit = wire_explicit_height_layer(out)
    kind = str(out.get("kind") or out.get("cell_kind") or "")
    transport = wire_transport_kind_for_layer_resolution(out)
    tile = str(out.get("tile_type") or out.get("sprite_identifier") or "")
    out["layer"] = resolve_replay_height_layer(
        cell_kind=kind,
        transport_kind=transport,
        tile_type=tile,
        layer=explicit,
    )
    return out


__all__ = [
    "clamp_replay_height_layer",
    "enrich_replay_wire_row_with_layer",
    "resolve_replay_height_layer",
    "wire_explicit_height_layer",
    "wire_transport_kind_for_layer_resolution",
]
