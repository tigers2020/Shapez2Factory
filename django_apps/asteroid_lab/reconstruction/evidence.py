"""Decoded-cell predicates for asteroid reconstruction walls (flood-fill obstacles)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.transport_components import is_transport_tile

ASTEROID_FIELD_KINDS: frozenset[str] = frozenset({"asteroid_fluid_field", "asteroid_shape_field"})

_BUILDING_CELL_KINDS: frozenset[str] = frozenset(
    {
        "fluid_miner",
        "fluid_miner_extension",
        "shape_miner",
        "shape_miner_extension",
    }
)

MINER_EXTENSION_CELL_KINDS: frozenset[str] = _BUILDING_CELL_KINDS


def is_strippable_building(cell: DecodedCellDTO) -> bool:
    """Transport, miners, and extensions are removed for reconstruction topology."""

    return is_transport_tile(cell) or cell.cell_kind in _BUILDING_CELL_KINDS


def is_asteroid_evidence(cell: DecodedCellDTO) -> bool:
    """Shell / mineable anchors from decode only (not replay-derived)."""

    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        return True
    if cell.cell_kind == "unknown":
        t = cell.tile_type
        if isinstance(t, str) and t.startswith("UnknownTile_"):
            return True
    return False


def evidence_field_kind(cell: DecodedCellDTO) -> str | None:
    """Mineable field kind for voting, or None if this evidence cell carries no fluid/shape hint."""

    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        return cell.cell_kind
    return None


def inferred_field_kind_from_removed_miner_extension(cell: DecodedCellDTO) -> str | None:
    """Field kind implied by a stripped miner/extension anchor (replay synthetic field parity)."""

    ck = cell.cell_kind
    if ck in ("fluid_miner", "fluid_miner_extension"):
        return "asteroid_fluid_field"
    if ck in ("shape_miner", "shape_miner_extension"):
        return "asteroid_shape_field"
    return None
