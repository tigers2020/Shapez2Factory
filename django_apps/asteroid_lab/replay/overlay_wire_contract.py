"""Replay overlay wire contract: occupancy transport vs output requirement."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from django_apps.asteroid_lab.replay.effective_cell_view import simulation_for_tile_id
from django_apps.asteroid_lab.replay.map_height_layer import enrich_replay_wire_row_with_layer
from django_apps.asteroid_lab.replay.replay_overlay_wire import ReplayOverlayCellWire
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell

OCCUPANCY_TRANSPORT_NONE = "none"
OUTPUT_TRANSPORT_NONE = "none"

CANDIDATE_OUTPUT_OVERLAY_KINDS = frozenset(
    {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
        "route_probe_path",
    }
)

_BANNED_CANDIDATE_OCCUPANCY_TRANSPORT = frozenset(
    {
        "space_belt",
        "space_pipe",
        "shape_belt",
        "fluid_pipe",
        "shape",
        "fluid",
        "belt",
        "pipe",
    }
)


_ALLOWED_PROFILE_TRANSPORT = frozenset({"none", "space_belt", "space_pipe"})


def profile_to_output_transport_kind(profile: str) -> str:
    """Map L3 transport profile tokens to replay output transport family."""

    value = str(profile or "").strip().lower()
    if not value or value == "none":
        return OUTPUT_TRANSPORT_NONE
    if value in _ALLOWED_PROFILE_TRANSPORT:
        return value
    msg = (
        "overlay profile transport must be none|space_belt|space_pipe; "
        f"legacy tokens must not reach overlay builders (got {profile!r})"
    )
    raise ValueError(msg)


def build_output_hint_overlay_cell(
    *,
    x: int,
    y: int,
    kind: str,
    profile_transport_kind: str,
    rotation: int = 0,
    layer: int | None = None,
) -> ReplayOverlayCell:
    """Overlay cell whose transport occupancy is empty but output family is declared."""

    return ReplayOverlayCell(
        x=x,
        y=y,
        kind=kind,
        transport=OCCUPANCY_TRANSPORT_NONE,
        output_transport_kind=profile_to_output_transport_kind(profile_transport_kind),
        rotation=rotation,
        layer=layer,
    )


def build_routed_transport_overlay_cell(
    *,
    x: int,
    y: int,
    transport_kind: str,
    tile_id: str,
    rotation: int = 0,
    layer: int | None = None,
) -> ReplayOverlayCell:
    """Overlay cell for a concrete routed space belt/pipe tile."""

    return ReplayOverlayCell(
        x=x,
        y=y,
        kind=transport_kind,
        transport=transport_kind,
        output_transport_kind=OUTPUT_TRANSPORT_NONE,
        tile_type=tile_id,
        rotation=rotation,
        layer=layer,
    )


def overlay_cell_to_wire_dict(cell: ReplayOverlayCell) -> ReplayOverlayCellWire:
    occupancy = str(cell.transport or OCCUPANCY_TRANSPORT_NONE)
    output = str(cell.output_transport_kind or OUTPUT_TRANSPORT_NONE)
    row: ReplayOverlayCellWire = {
        "x": int(cell.x),
        "y": int(cell.y),
        "kind": str(cell.kind),
        "transport": occupancy,
        "transport_kind": occupancy,
        "output_transport_kind": output,
        "tile_type": str(cell.tile_type),
        "rotation": int(cell.rotation),
    }
    if cell.layer is not None:
        row["layer"] = int(cell.layer)
    if cell.tile_type:
        simulation = simulation_for_tile_id(cell.tile_type)
        if simulation:
            row["simulation"] = simulation
    return cast(
        ReplayOverlayCellWire,
        enrich_replay_wire_row_with_layer(row),
    )


def assert_candidate_overlay_wire_contract(row: Mapping[str, Any]) -> None:
    kind = str(row.get("kind") or row.get("cell_kind") or "")
    if kind not in CANDIDATE_OUTPUT_OVERLAY_KINDS:
        return
    transport = str(row.get("transport") or row.get("transport_kind") or "").strip().lower()
    if transport in _BANNED_CANDIDATE_OCCUPANCY_TRANSPORT:
        msg = (
            f"candidate overlay kind={kind!r} must not claim transport occupancy "
            f"via transport={transport!r}; use output_transport_kind"
        )
        raise AssertionError(msg)


__all__ = [
    "CANDIDATE_OUTPUT_OVERLAY_KINDS",
    "OCCUPANCY_TRANSPORT_NONE",
    "OUTPUT_TRANSPORT_NONE",
    "assert_candidate_overlay_wire_contract",
    "build_output_hint_overlay_cell",
    "build_routed_transport_overlay_cell",
    "overlay_cell_to_wire_dict",
    "profile_to_output_transport_kind",
]
