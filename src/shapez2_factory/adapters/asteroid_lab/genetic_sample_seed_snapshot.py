"""``GeneticSampleSeedSnapshot`` — frozen JSON export of DB ``GeneSeed`` rows (no ORM)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

CURRENT_SCHEMA_VERSION = "genetic_sample_seed_v1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({CURRENT_SCHEMA_VERSION, "gene_catalog_v1"})
VALID_THROUGHPUT_FACTORS = frozenset({4, 8, 12, 16})
VALID_RESOURCE_KINDS = frozenset({"shape", "fluid", "both"})


class GeneticSampleSeedIssue(StrEnum):
    MISSING = "missing"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    MALFORMED = "malformed"


class GeneticSampleSeedInvalid(Exception):
    def __init__(self, issue: GeneticSampleSeedIssue, message: str) -> None:
        self.issue = issue
        super().__init__(f"{issue.value}: {message}")


@dataclass(frozen=True, slots=True)
class GeneticSampleSeedEntry:
    gene_id: str
    resource_kind: str
    canonical_output_dir: str
    occupied_offsets: tuple[tuple[int, int], ...]
    extractor_offset: tuple[int, int]
    extension_offsets: tuple[tuple[int, int], ...]
    output_stub_offset: tuple[int, int]
    route_probe_start_offset: tuple[int, int]
    throughput_factor: int
    topology_signature_base: str


@dataclass(frozen=True, slots=True)
class GeneticSampleSeedSnapshot:
    schema_version: str
    generated_at: str
    provenance_hash: str
    source_batch_id: str
    deterministic_sort_key: str
    entries: tuple[GeneticSampleSeedEntry, ...]

    @classmethod
    def from_payload(cls, payload: object) -> GeneticSampleSeedSnapshot:
        if not isinstance(payload, dict):
            raise GeneticSampleSeedInvalid(
                GeneticSampleSeedIssue.MALFORMED, "payload must be a JSON object"
            )
        schema_version = payload.get("schema_version")
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise GeneticSampleSeedInvalid(
                GeneticSampleSeedIssue.UNSUPPORTED_SCHEMA,
                f"schema_version {schema_version!r} not in {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise GeneticSampleSeedInvalid(
                GeneticSampleSeedIssue.MALFORMED, "entries must be a list"
            )
        entries = tuple(_parse_entry(e) for e in raw_entries)
        return cls(
            schema_version=str(schema_version),
            generated_at=str(payload.get("generated_at", "")),
            provenance_hash=str(payload.get("provenance_hash", "")),
            source_batch_id=str(payload.get("source_batch_id", "")),
            deterministic_sort_key=str(payload.get("deterministic_sort_key", "")),
            entries=entries,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> GeneticSampleSeedSnapshot:
        file_path = Path(path)
        if not file_path.is_file():
            raise GeneticSampleSeedInvalid(
                GeneticSampleSeedIssue.MISSING, f"file not found: {file_path}"
            )
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GeneticSampleSeedInvalid(
                GeneticSampleSeedIssue.MALFORMED, f"invalid JSON: {exc}"
            ) from exc
        return cls.from_payload(payload)


def _coord(value: object) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GeneticSampleSeedInvalid(GeneticSampleSeedIssue.MALFORMED, f"bad offset {value!r}")
    try:
        return (int(value[0]), int(value[1]))
    except (TypeError, ValueError) as exc:
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED, f"bad offset {value!r}"
        ) from exc


def _parse_entry(raw: object) -> GeneticSampleSeedEntry:
    if not isinstance(raw, dict):
        raise GeneticSampleSeedInvalid(GeneticSampleSeedIssue.MALFORMED, "entry must be an object")
    if "canonical_output_dir" not in raw:
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED, "entry missing canonical_output_dir"
        )
    output_dir = str(raw["canonical_output_dir"])
    if output_dir != "E":
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED,
            f"canonical_output_dir must be 'E', got {output_dir!r}",
        )
    resource_kind = str(raw.get("resource_kind", ""))
    if resource_kind not in VALID_RESOURCE_KINDS:
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED, f"bad resource_kind {resource_kind!r}"
        )
    try:
        throughput_factor = int(raw["throughput_factor"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED, "bad throughput_factor"
        ) from exc
    if throughput_factor not in VALID_THROUGHPUT_FACTORS:
        raise GeneticSampleSeedInvalid(
            GeneticSampleSeedIssue.MALFORMED,
            f"throughput_factor {throughput_factor} not allowed",
        )
    return GeneticSampleSeedEntry(
        gene_id=str(raw["gene_id"]),
        resource_kind=resource_kind,
        canonical_output_dir=output_dir,
        occupied_offsets=tuple(_coord(c) for c in raw.get("occupied_offsets", [])),
        extractor_offset=_coord(raw.get("extractor_offset", [0, 0])),
        extension_offsets=tuple(_coord(c) for c in raw.get("extension_offsets", [])),
        output_stub_offset=_coord(raw.get("output_stub_offset", [1, 0])),
        route_probe_start_offset=_coord(raw.get("route_probe_start_offset", [2, 0])),
        throughput_factor=throughput_factor,
        topology_signature_base=str(raw.get("topology_signature_base", "")),
    )


__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "GeneticSampleSeedEntry",
    "GeneticSampleSeedInvalid",
    "GeneticSampleSeedIssue",
    "GeneticSampleSeedSnapshot",
    "SUPPORTED_SCHEMA_VERSIONS",
]
