"""Replay cell semantic read policy — classify wire cell rows for Lab read paths."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.asteroid_lab.replay.replay_map_cell_wire import wire_field_kind

_LEGACY_SHAPE_OUTPUT_TOKENS = frozenset({"shape_belt", "belt", "shape"})
_LEGACY_FLUID_OUTPUT_TOKENS = frozenset({"fluid_pipe", "pipe", "fluid"})

SPACE_TILE_PREFIXES = ("SpaceBelt_", "SpacePipe_")
ROUTE_CELL_KINDS = frozenset({"space_belt", "space_pipe"})
OCCUPANT_CELL_KINDS = frozenset(
    {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
        "shape_miner",
        "fluid_miner",
        "shape_miner_extension",
        "fluid_miner_extension",
        "miner",
        "extension",
        "committed_miner",
        "building",
    }
)
TERRAIN_CELL_KINDS = frozenset(
    {
        "asteroid_shape_field",
        "asteroid_fluid_field",
        "void",
        "empty",
    }
)

OVERLAY_SEMANTIC_KINDS = frozenset(
    {
        "inner_field_block",
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
        "route_probe_path",
        "planned_exterior_connector",
    }
)

NORMALIZED_TRANSPORT_KINDS = frozenset({"none", "space_belt", "space_pipe"})


def normalize_project_transport_kind(raw: object) -> str:
    """Map legacy read tokens and plan aliases to canonical transport families."""

    value = str(raw or "").strip().lower()
    if not value or value == "none":
        return "none"
    if value in _LEGACY_SHAPE_OUTPUT_TOKENS or value == "space_belt":
        return "space_belt"
    if value in _LEGACY_FLUID_OUTPUT_TOKENS or value == "space_pipe":
        return "space_pipe"
    return "none"


def simulation_for_tile_id(tile_id: str | None) -> str | None:
    if not tile_id:
        return None
    if "Merger" in tile_id:
        return "SpaceMergerSimulation"
    if "Splitter" in tile_id:
        return "SpaceSplitterSimulation"
    if tile_id.startswith(SPACE_TILE_PREFIXES):
        return "SpaceConveyorSimulation"
    return None


def is_route_tile(tile_type: str, kind: str) -> bool:
    if tile_type.startswith(SPACE_TILE_PREFIXES):
        return True
    return kind in ROUTE_CELL_KINDS


def occupant_kind_from_cell(kind: str) -> str | None:
    if not kind:
        return None
    if kind not in OCCUPANT_CELL_KINDS:
        return None
    if kind in {"shape_miner", "fluid_miner", "miner"}:
        return "committed_miner"
    if kind in {"shape_miner_extension", "fluid_miner_extension", "extension"}:
        return "extension"
    return kind


def overlay_role_from_cell(cell: Mapping[str, object]) -> str | None:
    """Resolve overlay semantic role from explicit ``overlay_role`` or semantic ``kind``."""

    raw_role = cell.get("overlay_role")
    if raw_role is not None and str(raw_role).strip():
        return str(raw_role).strip()
    kind = wire_field_kind(cell).strip()
    if kind in OVERLAY_SEMANTIC_KINDS:
        return kind
    return None


def resolve_route_transport_kind(tile_type: str, kind: str, transport_raw: object) -> str:
    """Resolve route occupancy transport from kind, transport field, and tile prefix."""

    normalized = normalize_project_transport_kind(kind or transport_raw)
    if normalized != "none":
        return normalized
    if tile_type.startswith("SpacePipe_"):
        return "space_pipe"
    if tile_type.startswith("SpaceBelt_"):
        return "space_belt"
    return "none"


__all__ = [
    "NORMALIZED_TRANSPORT_KINDS",
    "OCCUPANT_CELL_KINDS",
    "OVERLAY_SEMANTIC_KINDS",
    "ROUTE_CELL_KINDS",
    "SPACE_TILE_PREFIXES",
    "TERRAIN_CELL_KINDS",
    "is_route_tile",
    "normalize_project_transport_kind",
    "occupant_kind_from_cell",
    "overlay_role_from_cell",
    "resolve_route_transport_kind",
    "simulation_for_tile_id",
]
