"""Import island SpaceBelt/SpacePipe catalog from ``documents/game_data`` JSON dumps."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


def _transport_kind(tile_id: str) -> str:
    return "space_pipe" if tile_id.startswith("SpacePipe_") else "space_belt"


def _group_id(transport_kind: str) -> str:
    return "SpacePipesGroup" if transport_kind == "space_pipe" else "SpaceBeltsGroup"


def _enumerate_tile_ids(research_unlocks_path: Path) -> tuple[str, ...]:
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


def _simulation_keys_by_tile(simulation_systems_path: Path) -> dict[str, str]:
    text = simulation_systems_path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for tile_id, key in _SIM_KEY_RE.findall(text):
        out.setdefault(tile_id, key)
    return out


def _routing_allowed(tile_id: str) -> bool:
    return "Lift" not in tile_id


def build_space_transport_catalog_payload(
    *,
    research_unlocks_path: str | Path,
    simulation_systems_path: str | Path,
    game_version: str = "",
    source_batch_id: str = "documents/game_data",
) -> dict[str, Any]:
    research_path = Path(research_unlocks_path)
    simulation_path = Path(simulation_systems_path)
    tile_ids = _enumerate_tile_ids(research_path)
    sim_keys = _simulation_keys_by_tile(simulation_path)
    entries: list[dict[str, Any]] = []
    for tile_id in tile_ids:
        transport_kind = _transport_kind(tile_id)
        entry: dict[str, Any] = {
            "tile_id": tile_id,
            "transport_kind": transport_kind,
            "group_id": _group_id(transport_kind),
            "canonical_rotation": 0,
            "allowed_rotations": [0, 1, 2, 3],
            "source_json_path": (
                "research_unlocks.json→Mode.Islands.DefinitionsById;"
                "simulation_systems.json→SpecializedIslandTenantSystemsByType"
            ),
            "routing_allowed": _routing_allowed(tile_id),
        }
        sim_key = sim_keys.get(tile_id)
        if sim_key is not None:
            entry["simulation_system_key"] = sim_key
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


def import_space_transport_catalog_from_game_data(
    *,
    research_unlocks_path: str | Path,
    simulation_systems_path: str | Path,
    game_version: str = "",
) -> dict[str, Any]:
    """Build a catalog payload suitable for ``SpaceTransportTileCatalog.from_payload``."""
    return build_space_transport_catalog_payload(
        research_unlocks_path=research_unlocks_path,
        simulation_systems_path=simulation_systems_path,
        game_version=game_version,
    )


__all__ = [
    "build_space_transport_catalog_payload",
    "import_space_transport_catalog_from_game_data",
]
