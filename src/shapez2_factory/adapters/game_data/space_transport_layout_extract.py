"""Extract island ``SpaceBelt_*`` / ``SpacePipe_*`` layout catalog from game_data JSON dumps."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    CURRENT_SCHEMA_VERSION,
)

_TILE_ID_RE = re.compile(r"^Space(?:Belt|Pipe)_\w+$")
_SIM_KEY_RE = re.compile(r'"(Space(?:Belt|Pipe)_\w+)":\["([^"]+)"\]')

# R0_E_CW curated I/O (E,S,W,N). Extend via visual oracle before golden Turn/Merger tests.
_IoMaskPair = tuple[tuple[bool, bool, bool, bool], tuple[bool, bool, bool, bool]]
_R0_IO_SIGNATURES: dict[str, _IoMaskPair] = {
    "SpaceBelt_Forward": ((False, False, True, False), (True, False, False, False)),
    "SpacePipe_Forward": ((False, False, True, False), (True, False, False, False)),
    "SpaceBelt_LeftTurn": ((False, False, True, False), (False, False, False, True)),
    "SpacePipe_LeftTurn": ((False, False, True, False), (False, False, False, True)),
    "SpaceBelt_RightTurn": ((False, False, True, False), (False, True, False, False)),
    "SpacePipe_RightTurn": ((False, False, True, False), (False, True, False, False)),
}


def transport_kind_for_tile_id(tile_id: str) -> str:
    return "space_pipe" if tile_id.startswith("SpacePipe_") else "space_belt"


def group_id_for_transport_kind(transport_kind: str) -> str:
    return "SpacePipesGroup" if transport_kind == "space_pipe" else "SpaceBeltsGroup"


def layout_suffix_for_tile_id(tile_id: str) -> str:
    if tile_id.startswith("SpaceBelt_"):
        return tile_id.removeprefix("SpaceBelt_")
    if tile_id.startswith("SpacePipe_"):
        return tile_id.removeprefix("SpacePipe_")
    return tile_id


def simulation_family_from_key(simulation_system_key: str) -> str:
    key = simulation_system_key or ""
    if "Merger" in key:
        return "merger"
    if "Splitter" in key:
        return "splitter"
    return "conveyor"


def eswn_mask_to_string(mask: tuple[bool, bool, bool, bool]) -> str:
    return "".join("1" if bit else "0" for bit in mask)


def enumerate_space_transport_tile_ids(research_unlocks_path: Path) -> tuple[str, ...]:
    payload = json.loads(research_unlocks_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("research_unlocks.json: expected non-empty list root")
    manager = payload[0].get("manager_snapshot", {})
    mode = manager.get("Mode", {})
    islands = mode.get("Islands", {})
    definitions = islands.get("DefinitionsById", {})
    if not isinstance(definitions, dict):
        raise ValueError("research_unlocks.json: missing Mode.Islands.DefinitionsById")
    return tuple(sorted(k for k in definitions if _TILE_ID_RE.match(k)))


def simulation_keys_by_tile(simulation_systems_path: Path) -> dict[str, str]:
    text = simulation_systems_path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for tile_id, key in _SIM_KEY_RE.findall(text):
        out.setdefault(tile_id, key)
    return out


def routing_allowed_for_tile_id(tile_id: str) -> bool:
    return "Lift" not in tile_id


def build_space_transport_catalog_payload(
    *,
    research_unlocks_path: str | Path,
    simulation_systems_path: str | Path,
    game_version: str = "",
    source_batch_id: str = "documents/game_data",
) -> dict[str]:
    research_path = Path(research_unlocks_path)
    simulation_path = Path(simulation_systems_path)
    tile_ids = enumerate_space_transport_tile_ids(research_path)
    sim_keys = simulation_keys_by_tile(simulation_path)
    entries: list[dict[str]] = []
    for tile_id in tile_ids:
        transport_kind = transport_kind_for_tile_id(tile_id)
        entry: dict[str] = {
            "tile_id": tile_id,
            "transport_kind": transport_kind,
            "group_id": group_id_for_transport_kind(transport_kind),
            "layout_suffix": layout_suffix_for_tile_id(tile_id),
            "canonical_rotation": 0,
            "allowed_rotations": [0, 1, 2, 3],
            "source_json_path": (
                "research_unlocks.json→Mode.Islands.DefinitionsById;"
                "simulation_systems.json→SpecializedIslandTenantSystemsByType"
            ),
            "routing_allowed": routing_allowed_for_tile_id(tile_id),
        }
        sim_key = sim_keys.get(tile_id)
        if sim_key is not None:
            entry["simulation_system_key"] = sim_key
            entry["simulation_family"] = simulation_family_from_key(sim_key)
        io = _R0_IO_SIGNATURES.get(tile_id)
        if io is not None:
            entry["input_mask_eswn"] = list(io[0])
            entry["output_mask_eswn"] = list(io[1])
        entries.append(entry)
    provenance = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()[:16]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "game_version": game_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "provenance_hash": provenance,
        "source_batch_id": source_batch_id,
        "entries": entries,
    }


__all__ = [
    "build_space_transport_catalog_payload",
    "enumerate_space_transport_tile_ids",
    "eswn_mask_to_string",
    "group_id_for_transport_kind",
    "layout_suffix_for_tile_id",
    "routing_allowed_for_tile_id",
    "simulation_family_from_key",
    "simulation_keys_by_tile",
    "transport_kind_for_tile_id",
]
