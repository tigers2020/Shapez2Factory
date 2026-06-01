"""``SpaceTransportTileCatalog`` — frozen JSON export of island transport tiles (no ORM)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

CURRENT_SCHEMA_VERSION = "space_transport_catalog_v1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({CURRENT_SCHEMA_VERSION})
VALID_TRANSPORT_KINDS = frozenset({"space_belt", "space_pipe"})

# E, S, W, N (R0_E_CW)
EswmMask = tuple[bool, bool, bool, bool]


class SpaceTransportCatalogIssue(StrEnum):
    MISSING = "missing"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    MALFORMED = "malformed"
    LOOKUP_MISS = "lookup_miss"


class SpaceTransportCatalogInvalid(Exception):
    def __init__(self, issue: SpaceTransportCatalogIssue, message: str) -> None:
        self.issue = issue
        super().__init__(f"{issue.value}: {message}")


@dataclass(frozen=True, slots=True)
class TransportIoSignature:
    transport_kind: str
    input_mask_eswn: EswmMask
    output_mask_eswn: EswmMask


@dataclass(frozen=True, slots=True)
class SpaceTransportTileCatalogEntry:
    tile_id: str
    transport_kind: str
    group_id: str
    io_signature: TransportIoSignature | None
    canonical_rotation: int
    allowed_rotations: tuple[int, ...]
    simulation_system_key: str | None
    source_json_path: str
    routing_allowed: bool


@dataclass(frozen=True, slots=True)
class SpaceTransportTileCatalog:
    schema_version: str
    game_version: str
    generated_at: str
    provenance_hash: str
    source_batch_id: str
    entries: tuple[SpaceTransportTileCatalogEntry, ...]
    _by_tile_id: dict[str, SpaceTransportTileCatalogEntry]
    _by_io: dict[tuple[str, EswmMask, EswmMask], SpaceTransportTileCatalogEntry]

    @classmethod
    def from_payload(cls, payload: object) -> SpaceTransportTileCatalog:
        if not isinstance(payload, dict):
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.MALFORMED, "payload must be a JSON object"
            )
        schema_version = payload.get("schema_version")
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.UNSUPPORTED_SCHEMA,
                f"schema_version {schema_version!r} not in {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.MALFORMED, "entries must be a list"
            )
        entries = tuple(_parse_entry(raw) for raw in raw_entries)
        by_tile: dict[str, SpaceTransportTileCatalogEntry] = {}
        by_io: dict[tuple[str, EswmMask, EswmMask], SpaceTransportTileCatalogEntry] = {}
        for entry in entries:
            if entry.tile_id in by_tile:
                raise SpaceTransportCatalogInvalid(
                    SpaceTransportCatalogIssue.MALFORMED,
                    f"duplicate tile_id {entry.tile_id!r}",
                )
            by_tile[entry.tile_id] = entry
            if entry.io_signature is not None:
                sig = entry.io_signature
                key = (sig.transport_kind, sig.input_mask_eswn, sig.output_mask_eswn)
                if key in by_io:
                    raise SpaceTransportCatalogInvalid(
                        SpaceTransportCatalogIssue.MALFORMED,
                        f"duplicate io signature for {entry.tile_id!r}",
                    )
                by_io[key] = entry
        return cls(
            schema_version=str(schema_version),
            game_version=str(payload.get("game_version", "")),
            generated_at=str(payload.get("generated_at", "")),
            provenance_hash=str(payload.get("provenance_hash", "")),
            source_batch_id=str(payload.get("source_batch_id", "")),
            entries=entries,
            _by_tile_id=by_tile,
            _by_io=by_io,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> SpaceTransportTileCatalog:
        file_path = Path(path)
        if not file_path.is_file():
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.MISSING, f"catalog file not found: {file_path}"
            )
        return cls.from_payload(json.loads(file_path.read_text(encoding="utf-8")))

    def lookup_io(
        self,
        *,
        transport_kind: str,
        input_mask: EswmMask,
        output_mask: EswmMask,
    ) -> SpaceTransportTileCatalogEntry:
        if transport_kind not in VALID_TRANSPORT_KINDS:
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.LOOKUP_MISS,
                f"unknown transport_kind {transport_kind!r}",
            )
        key = (transport_kind, input_mask, output_mask)
        entry = self._by_io.get(key)
        if entry is None:
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.LOOKUP_MISS,
                "no catalog entry for transport_kind="
                f"{transport_kind!r} input={input_mask!r} output={output_mask!r}",
            )
        return entry

    def lookup_tile_id(self, tile_id: str) -> SpaceTransportTileCatalogEntry:
        entry = self._by_tile_id.get(tile_id)
        if entry is None:
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.LOOKUP_MISS,
                f"no catalog entry for tile_id={tile_id!r}",
            )
        return entry

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "game_version": self.game_version,
            "generated_at": self.generated_at,
            "provenance_hash": self.provenance_hash,
            "source_batch_id": self.source_batch_id,
            "entries": [_entry_to_dict(e) for e in self.entries],
        }


def _parse_bool_mask(raw: object, *, field: str) -> EswmMask:
    if not isinstance(raw, list) or len(raw) != 4:
        raise SpaceTransportCatalogInvalid(
            SpaceTransportCatalogIssue.MALFORMED,
            f"{field} must be a list of 4 booleans (E,S,W,N)",
        )
    return tuple(bool(v) for v in raw)


def _parse_entry(raw: object) -> SpaceTransportTileCatalogEntry:
    if not isinstance(raw, dict):
        raise SpaceTransportCatalogInvalid(
            SpaceTransportCatalogIssue.MALFORMED, "entry must be an object"
        )
    tile_id = str(raw.get("tile_id", ""))
    if not tile_id:
        raise SpaceTransportCatalogInvalid(
            SpaceTransportCatalogIssue.MALFORMED, "tile_id is required"
        )
    transport_kind = str(raw.get("transport_kind", ""))
    if transport_kind not in VALID_TRANSPORT_KINDS:
        raise SpaceTransportCatalogInvalid(
            SpaceTransportCatalogIssue.MALFORMED,
            f"invalid transport_kind {transport_kind!r} on {tile_id}",
        )
    group_id = str(raw.get("group_id", ""))
    has_input = "input_mask_eswn" in raw
    has_output = "output_mask_eswn" in raw
    io_signature: TransportIoSignature | None
    if has_input or has_output:
        if not (has_input and has_output):
            raise SpaceTransportCatalogInvalid(
                SpaceTransportCatalogIssue.MALFORMED,
                f"{tile_id}: input_mask_eswn and output_mask_eswn must both be set",
            )
        io_signature = TransportIoSignature(
            transport_kind=transport_kind,
            input_mask_eswn=_parse_bool_mask(raw["input_mask_eswn"], field="input_mask_eswn"),
            output_mask_eswn=_parse_bool_mask(raw["output_mask_eswn"], field="output_mask_eswn"),
        )
    else:
        io_signature = None
    allowed_raw = raw.get("allowed_rotations", [0])
    if not isinstance(allowed_raw, list) or not allowed_raw:
        raise SpaceTransportCatalogInvalid(
            SpaceTransportCatalogIssue.MALFORMED,
            f"{tile_id}: allowed_rotations must be a non-empty list",
        )
    return SpaceTransportTileCatalogEntry(
        tile_id=tile_id,
        transport_kind=transport_kind,
        group_id=group_id,
        io_signature=io_signature,
        canonical_rotation=int(raw.get("canonical_rotation", 0)),
        allowed_rotations=tuple(int(r) for r in allowed_raw),
        simulation_system_key=(
            str(raw["simulation_system_key"]) if raw.get("simulation_system_key") else None
        ),
        source_json_path=str(raw.get("source_json_path", "")),
        routing_allowed=bool(raw.get("routing_allowed", True)),
    )


def _entry_to_dict(entry: SpaceTransportTileCatalogEntry) -> dict[str, Any]:
    out: dict[str, Any] = {
        "tile_id": entry.tile_id,
        "transport_kind": entry.transport_kind,
        "group_id": entry.group_id,
        "canonical_rotation": entry.canonical_rotation,
        "allowed_rotations": list(entry.allowed_rotations),
        "source_json_path": entry.source_json_path,
        "routing_allowed": entry.routing_allowed,
    }
    if entry.simulation_system_key is not None:
        out["simulation_system_key"] = entry.simulation_system_key
    if entry.io_signature is not None:
        out["input_mask_eswn"] = list(entry.io_signature.input_mask_eswn)
        out["output_mask_eswn"] = list(entry.io_signature.output_mask_eswn)
    return out


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "EswmMask",
    "SpaceTransportCatalogInvalid",
    "SpaceTransportCatalogIssue",
    "SpaceTransportTileCatalog",
    "SpaceTransportTileCatalogEntry",
    "TransportIoSignature",
]
