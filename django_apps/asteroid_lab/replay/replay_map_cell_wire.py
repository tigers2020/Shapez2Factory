"""Replay map cell wire shapes and DTO ingress/egress (full_cells / cell_delta / overlay)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict, cast

from django_apps.asteroid_lab.replay.map_height_layer import (
    enrich_replay_wire_row_with_layer,
    wire_explicit_height_layer,
)
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayCell,
    ReplayCellDelta,
    ReplayOverlayCell,
)


class ReplayMapCellWireError(ValueError):
    """Raised when a replay map cell wire row violates the shared contract."""

    def __init__(self, message: str, *, field: str = "") -> None:
        super().__init__(message)
        self.field = field


class ReplayCellWire(TypedDict):
    """One full snapshot cell row in replay timeline map_view wire."""

    x: int
    y: int
    kind: str
    transport: str
    tile_type: str
    sprite_identifier: str
    rotation: int
    layer: NotRequired[int]


class ReplayCellDeltaWire(TypedDict):
    """One materialized cell_delta row in replay timeline map_view wire."""

    x: int
    y: int
    kind: str
    transport: str
    op: str
    tile_type: str
    sprite_identifier: str
    rotation: int
    layer: NotRequired[int]


def wire_field_kind(data: Mapping[str, object]) -> str:
    """Read cell kind from wire, accepting legacy ``cell_kind`` alias."""

    return str(data.get("kind") or data.get("cell_kind") or "")


def wire_field_transport(data: Mapping[str, object]) -> str:
    """Read transport from wire, accepting legacy ``transport_kind`` alias."""

    return str(data.get("transport") or data.get("transport_kind") or "")


def wire_field_tile_type(data: Mapping[str, object]) -> str:
    """Read tile id from wire, accepting legacy ``sprite_identifier`` alias."""

    return str(data.get("tile_type") or data.get("sprite_identifier") or "")


def _require_wire_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReplayMapCellWireError(f"{field} must be int", field=field)
    return value


def _coerce_wire_rotation(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    return default


def _rotation_from_wire(
    raw: Mapping[str, object],
    *,
    field: str,
    lenient_rotation: bool,
) -> int:
    value = raw.get("rotation")
    if lenient_rotation:
        return _coerce_wire_rotation(value)
    return _require_wire_int(value, field=field)


def replay_cell_from_wire(
    raw: Mapping[str, object],
    *,
    field_prefix: str = "cell",
    lenient_rotation: bool = True,
) -> ReplayCell:
    """Deserialize one full snapshot cell wire row into a semantic DTO."""

    if not isinstance(raw, dict):
        label = f"{field_prefix} wire" if field_prefix else "cell wire"
        raise ReplayMapCellWireError(f"{label} must be object")

    prefix = f"{field_prefix}." if field_prefix else ""
    return ReplayCell(
        x=_require_wire_int(raw.get("x"), field=f"{prefix}x"),
        y=_require_wire_int(raw.get("y"), field=f"{prefix}y"),
        kind=wire_field_kind(raw),
        transport=wire_field_transport(raw),
        tile_type=wire_field_tile_type(raw),
        rotation=_rotation_from_wire(
            raw,
            field=f"{prefix}rotation",
            lenient_rotation=lenient_rotation,
        ),
        layer=wire_explicit_height_layer(raw),
    )


def replay_cell_delta_from_wire(
    raw: Mapping[str, object],
    *,
    field_prefix: str = "cell_delta",
    lenient_rotation: bool = True,
) -> ReplayCellDelta:
    """Deserialize one cell_delta wire row into a semantic DTO."""

    if not isinstance(raw, dict):
        label = f"{field_prefix} wire" if field_prefix else "cell_delta wire"
        raise ReplayMapCellWireError(f"{label} must be object")

    prefix = f"{field_prefix}." if field_prefix else ""
    return ReplayCellDelta(
        x=_require_wire_int(raw.get("x"), field=f"{prefix}x"),
        y=_require_wire_int(raw.get("y"), field=f"{prefix}y"),
        kind=wire_field_kind(raw),
        transport=wire_field_transport(raw),
        op=str(raw.get("op") or "set"),
        tile_type=wire_field_tile_type(raw),
        rotation=_rotation_from_wire(
            raw,
            field=f"{prefix}rotation",
            lenient_rotation=lenient_rotation,
        ),
        layer=wire_explicit_height_layer(raw),
    )


def replay_overlay_cell_from_wire(
    raw: Mapping[str, object],
    *,
    field_prefix: str = "overlay",
    lenient_rotation: bool = True,
) -> ReplayOverlayCell:
    """Deserialize one overlay cell wire row into a semantic DTO."""

    if not isinstance(raw, dict):
        label = f"{field_prefix} wire" if field_prefix else "overlay wire"
        raise ReplayMapCellWireError(f"{label} must be object")

    prefix = f"{field_prefix}." if field_prefix else ""
    return ReplayOverlayCell(
        x=_require_wire_int(raw.get("x"), field=f"{prefix}x"),
        y=_require_wire_int(raw.get("y"), field=f"{prefix}y"),
        kind=wire_field_kind(raw),
        transport=wire_field_transport(raw),
        output_transport_kind=str(raw.get("output_transport_kind") or ""),
        tile_type=wire_field_tile_type(raw),
        rotation=_rotation_from_wire(
            raw,
            field=f"{prefix}rotation",
            lenient_rotation=lenient_rotation,
        ),
        layer=wire_explicit_height_layer(raw),
    )


def _snapshot_cell_wire_row(
    *,
    x: int,
    y: int,
    kind: str,
    transport: str,
    tile_type: str,
    rotation: int,
    layer: int | None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "x": int(x),
        "y": int(y),
        "kind": str(kind),
        "transport": str(transport),
        "tile_type": str(tile_type),
        "sprite_identifier": str(tile_type),
        "rotation": int(rotation),
    }
    if layer is not None:
        row["layer"] = int(layer)
    return row


def replay_cell_to_wire(cell: ReplayCell) -> ReplayCellWire:
    """Serialize one full snapshot cell to timeline wire with resolved layer."""

    row = _snapshot_cell_wire_row(
        x=cell.x,
        y=cell.y,
        kind=cell.kind,
        transport=cell.transport,
        tile_type=cell.tile_type,
        rotation=cell.rotation,
        layer=cell.layer,
    )
    return cast(ReplayCellWire, enrich_replay_wire_row_with_layer(row))


def replay_cell_delta_to_wire(delta: ReplayCellDelta) -> ReplayCellDeltaWire:
    """Serialize one cell_delta row to timeline wire with resolved layer."""

    row = _snapshot_cell_wire_row(
        x=delta.x,
        y=delta.y,
        kind=delta.kind,
        transport=delta.transport,
        tile_type=delta.tile_type,
        rotation=delta.rotation,
        layer=delta.layer,
    )
    row["op"] = str(delta.op)
    return cast(ReplayCellDeltaWire, enrich_replay_wire_row_with_layer(row))


__all__ = [
    "ReplayCellDeltaWire",
    "ReplayCellWire",
    "ReplayMapCellWireError",
    "replay_cell_delta_from_wire",
    "replay_cell_delta_to_wire",
    "replay_cell_from_wire",
    "replay_cell_to_wire",
    "replay_overlay_cell_from_wire",
    "wire_field_kind",
    "wire_field_tile_type",
    "wire_field_transport",
]
