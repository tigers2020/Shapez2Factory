"""Constants for miner seed ingest and projection (GeneticSample DB canonical)."""

from __future__ import annotations

MINER_SEED_SCHEMA = "miner_seed_v1"
EXHAUSTIVE_GENERATOR_STALE = "exhaustive_sample_gene_v1"
DEFAULT_BOOTSTRAP_PATH = "var/default_miner_pattern.txt"

MINER_LAYOUT_TYPES_SHAPE = (
    "Layout_ShapeMiner",
    "Layout_ShapeMinerExtension",
    "SpaceBelt_Forward",
)

LAYOUT_TYPE_SHAPE_TO_FLUID: dict[str, str] = {
    "Layout_ShapeMiner": "Layout_FluidMiner",
    "Layout_ShapeMinerExtension": "Layout_FluidMinerExtension",
    "SpaceBelt_Forward": "SpacePipe_Forward",
}


def gene_key_for_rank(rank: int) -> str:
    if rank < 1 or rank > 14:
        msg = "seed rank must be 1..14"
        raise ValueError(msg)
    return f"miner_seed_{rank:02d}"


__all__ = [
    "DEFAULT_BOOTSTRAP_PATH",
    "EXHAUSTIVE_GENERATOR_STALE",
    "LAYOUT_TYPE_SHAPE_TO_FLUID",
    "MINER_LAYOUT_TYPES_SHAPE",
    "MINER_SEED_SCHEMA",
    "gene_key_for_rank",
]
