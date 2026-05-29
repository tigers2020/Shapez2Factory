"""Miner seed catalog loader (GeneticSample ORM + in-memory fixtures)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
from django_apps.asteroid_lab.models import GeneticSample


@dataclass(frozen=True, slots=True)
class MinerSeedEntry:
    gene_key: str
    pattern_id: str
    intrinsic_priority_rank: int
    throughput_factor: int
    topology_signature: str
    decoded_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MinerSeedCatalog:
    seeds: tuple[MinerSeedEntry, ...]

    def by_intrinsic_priority_rank(self) -> tuple[MinerSeedEntry, ...]:
        return self.seeds

    @classmethod
    def from_entries(cls, *entries: MinerSeedEntry) -> MinerSeedCatalog:
        ordered = tuple(sorted(entries, key=lambda e: (e.intrinsic_priority_rank, e.gene_key)))
        return cls(seeds=ordered)


def _entry_from_genetic_sample(row: GeneticSample) -> MinerSeedEntry | None:
    meta = row.metadata_json if isinstance(row.metadata_json, dict) else {}
    if meta.get("schema") != MINER_SEED_SCHEMA_V2 or not meta.get("is_seed"):
        return None
    pattern_id = meta.get("pattern_id")
    intrinsic_priority_rank = meta.get("intrinsic_priority_rank")
    throughput_factor = meta.get("throughput_factor")
    topology_signature = meta.get("topology_signature")
    gene_key = row.gene_key or ""
    if (
        not isinstance(pattern_id, str)
        or not isinstance(intrinsic_priority_rank, int)
        or not isinstance(throughput_factor, int)
        or not isinstance(topology_signature, str)
        or not gene_key
    ):
        return None
    decoded = row.decoded_json if isinstance(row.decoded_json, dict) else {}
    return MinerSeedEntry(
        gene_key=gene_key,
        pattern_id=pattern_id,
        intrinsic_priority_rank=intrinsic_priority_rank,
        throughput_factor=throughput_factor,
        topology_signature=topology_signature,
        decoded_json=decoded,
    )


def load_miner_seed_catalog() -> MinerSeedCatalog:
    entries: list[MinerSeedEntry] = []
    for row in GeneticSample.objects.filter(
        gene_key__isnull=False,
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    ).order_by("gene_key"):
        parsed = _entry_from_genetic_sample(row)
        if parsed is not None:
            entries.append(parsed)
    entries.sort(key=lambda e: (e.intrinsic_priority_rank, e.gene_key))
    return MinerSeedCatalog(seeds=tuple(entries))


__all__ = [
    "MinerSeedCatalog",
    "MinerSeedEntry",
    "load_miner_seed_catalog",
]
