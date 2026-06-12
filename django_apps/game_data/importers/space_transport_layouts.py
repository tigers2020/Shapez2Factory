"""Import island SpaceBelt/SpacePipe layouts into ``SpaceTransportLayoutRegistry``."""

from __future__ import annotations

from pathlib import Path

from django_apps.game_data.importers.base import ImportContext
from django_apps.game_data.models import SpaceTransportLayoutRegistry
from django_apps.game_data.services import identifiers
from shapez2_factory.adapters.game_data.space_transport_layout_extract import (
    build_space_transport_catalog_payload,
    eswn_mask_to_string,
    simulation_family_from_key,
)


def _mask_field(raw: object) -> tuple[bool, str]:
    if not isinstance(raw, list) or len(raw) != 4:
        return False, ""
    bits = tuple(bool(x) for x in raw)
    return True, eswn_mask_to_string(bits)


def import_space_transport_layouts(
    ctx: ImportContext,
    *,
    research_unlocks_path: Path,
    simulation_systems_path: Path,
    game_version: str = "",
) -> None:
    payload = build_space_transport_catalog_payload(
        research_unlocks_path=research_unlocks_path,
        simulation_systems_path=simulation_systems_path,
        game_version=game_version,
        source_batch_id=str(ctx.batch.pk),
    )
    entries: list[dict[str, object]] = payload.get("entries") or []
    if len(entries) != 54:
        msg = f"expected 54 space transport layouts, got {len(entries)}"
        raise ValueError(msg)

    for index, entry in enumerate(entries):
        tile_id = str(entry.get("tile_id", "")).strip()
        if not tile_id:
            continue
        transport_kind = str(entry.get("transport_kind", "")).strip()
        sim_key = str(entry.get("simulation_system_key", "") or "")
        sim_family = str(entry.get("simulation_family", "") or "")
        if not sim_family and sim_key:
            sim_family = simulation_family_from_key(sim_key)

        has_io, input_mask = _mask_field(entry.get("input_mask_eswn"))
        has_io_out, output_mask = _mask_field(entry.get("output_mask_eswn"))
        has_io_signature = has_io and has_io_out

        rotations = entry.get("allowed_rotations")
        if isinstance(rotations, list) and rotations:
            allowed_rotations = ",".join(str(int(r)) for r in rotations)
        else:
            allowed_rotations = "0,1,2,3"

        cid = identifiers.canonical_space_transport_layout(tile_id)
        SpaceTransportLayoutRegistry.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": ctx.batch,
                "tile_id": tile_id,
                "transport_kind": transport_kind,
                "group_id": str(entry.get("group_id", "")),
                "layout_suffix": str(entry.get("layout_suffix", "")),
                "simulation_system_key": sim_key,
                "simulation_family": sim_family,
                "routing_allowed": bool(entry.get("routing_allowed", True)),
                "canonical_rotation": int(entry.get("canonical_rotation", 0)),
                "allowed_rotations": allowed_rotations,
                "has_io_signature": has_io_signature,
                "input_mask_eswn": input_mask if has_io_signature else "",
                "output_mask_eswn": output_mask if has_io_signature else "",
                "source_row_index": index,
            },
        )
        ctx.bump("space_transport_layout_registry")


__all__ = ["import_space_transport_layouts"]
