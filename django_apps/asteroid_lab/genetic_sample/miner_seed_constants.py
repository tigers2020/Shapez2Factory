"""Constants for miner seed ingest and projection (GeneticSample DB canonical)."""

from __future__ import annotations

MINER_SEED_SCHEMA = "miner_seed_v1"
MINER_SEED_SCHEMA_V2 = "miner_seed_v2"
EXHAUSTIVE_GENERATOR_STALE = "exhaustive_sample_gene_v1"

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

EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER: tuple[str, ...] = (
    "m3e_01",
    "m3e_02",
    "m3e_04",
    "m2e_01",
    "m3e_03",
    "m2e_02",
    "m3e_07",
    "m3e_09",
    "m3e_06",
    "m3e_13",
    "m3e_05",
    "m3e_11",
    "m3e_12",
    "m3e_08",
    "m2e_04",
    "m2e_03",
    "m1e_01",
    "m0e_01",
)

EXPECTED_DIFFICULTY_RANK_ORDER: tuple[str, ...] = (
    "m0e_01",
    "m1e_01",
    "m2e_01",
    "m2e_02",
    "m2e_04",
    "m2e_03",
    "m3e_01",
    "m3e_02",
    "m3e_04",
    "m3e_03",
    "m3e_07",
    "m3e_09",
    "m3e_06",
    "m3e_13",
    "m3e_05",
    "m3e_11",
    "m3e_12",
    "m3e_08",
)

EXPECTED_PATTERN_IDS: tuple[str, ...] = (
    "m0e_01",
    "m1e_01",
    "m2e_01",
    "m2e_02",
    "m2e_03",
    "m2e_04",
    "m3e_01",
    "m3e_02",
    "m3e_03",
    "m3e_04",
    "m3e_05",
    "m3e_06",
    "m3e_07",
    "m3e_08",
    "m3e_09",
    "m3e_11",
    "m3e_12",
    "m3e_13",
)

# Audit md lists m3e_10 as a parent-R variant of m3e_09 (same equivalence class).
AUDIT_ONLY_PATTERN_IDS: frozenset[str] = frozenset({"m3e_10"})

EXPECTED_MINER_SEED_GENE_KEYS: tuple[str, ...] = tuple(
    f"miner_seed_{pattern_id}" for pattern_id in EXPECTED_PATTERN_IDS
)

# Back-compat alias (18 canonical keys after m3e_10 collapse).
EXPECTED_19_GENE_KEYS: tuple[str, ...] = EXPECTED_MINER_SEED_GENE_KEYS

MINER_SEED_SCHEMAS_PURGEABLE: frozenset[str] = frozenset({MINER_SEED_SCHEMA, MINER_SEED_SCHEMA_V2})


def gene_key_for_pattern_id(pattern_id: str) -> str:
    if pattern_id not in EXPECTED_PATTERN_IDS:
        msg = f"unknown miner seed pattern_id: {pattern_id!r}"
        raise ValueError(msg)
    return f"miner_seed_{pattern_id}"


def gene_key_for_rank(rank: int) -> str:
    """Legacy v1 rank 1..14 — retained for tests referencing old keys only."""

    if rank < 1 or rank > 14:
        msg = "legacy seed rank must be 1..14"
        raise ValueError(msg)
    return f"miner_seed_{rank:02d}"


CANONICAL_MINER_SEED_GENE_KEYS: tuple[str, ...] = EXPECTED_MINER_SEED_GENE_KEYS

CANONICAL_MINER_SEED_COUNT = len(EXPECTED_PATTERN_IDS)


__all__ = [
    "AUDIT_ONLY_PATTERN_IDS",
    "CANONICAL_MINER_SEED_COUNT",
    "CANONICAL_MINER_SEED_GENE_KEYS",
    "EXPECTED_19_GENE_KEYS",
    "EXPECTED_DIFFICULTY_RANK_ORDER",
    "EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER",
    "EXPECTED_MINER_SEED_GENE_KEYS",
    "EXPECTED_PATTERN_IDS",
    "EXHAUSTIVE_GENERATOR_STALE",
    "LAYOUT_TYPE_SHAPE_TO_FLUID",
    "MINER_LAYOUT_TYPES_SHAPE",
    "MINER_SEED_SCHEMA",
    "MINER_SEED_SCHEMA_V2",
    "MINER_SEED_SCHEMAS_PURGEABLE",
    "gene_key_for_pattern_id",
    "gene_key_for_rank",
]
