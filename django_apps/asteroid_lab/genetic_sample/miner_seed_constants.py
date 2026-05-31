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

# Canonical per-pattern metrics (single source of truth). Insertion order = catalog order.
# Values mirror the runtime intrinsic-difficulty computation that ``seed_miner_patterns``
# writes into ``GeneticSample.metadata_json``; the DB rows are derived from these.
PatternMetrics = dict[str, int]

EXPECTED_PATTERN_METRICS: dict[str, PatternMetrics] = {
    "m0e_01": {
        "difficulty_rank": 1,
        "difficulty_score": 8,
        "difficulty_tier": 0,
        "intrinsic_priority_rank": 18,
        "intrinsic_priority_score": 420,
    },
    "m1e_01": {
        "difficulty_rank": 2,
        "difficulty_score": 105,
        "difficulty_tier": 1,
        "intrinsic_priority_rank": 17,
        "intrinsic_priority_score": 351,
    },
    "m2e_01": {
        "difficulty_rank": 3,
        "difficulty_score": 221,
        "difficulty_tier": 2,
        "intrinsic_priority_rank": 4,
        "intrinsic_priority_score": 224,
    },
    "m2e_02": {
        "difficulty_rank": 4,
        "difficulty_score": 233,
        "difficulty_tier": 2,
        "intrinsic_priority_rank": 6,
        "intrinsic_priority_score": 234,
    },
    "m2e_03": {
        "difficulty_rank": 6,
        "difficulty_score": 263,
        "difficulty_tier": 3,
        "intrinsic_priority_rank": 16,
        "intrinsic_priority_score": 259,
    },
    "m2e_04": {
        "difficulty_rank": 5,
        "difficulty_score": 261,
        "difficulty_tier": 3,
        "intrinsic_priority_rank": 15,
        "intrinsic_priority_score": 258,
    },
    "m3e_01": {
        "difficulty_rank": 7,
        "difficulty_score": 337,
        "difficulty_tier": 4,
        "intrinsic_priority_rank": 1,
        "intrinsic_priority_score": 211,
    },
    "m3e_02": {
        "difficulty_rank": 8,
        "difficulty_score": 354,
        "difficulty_tier": 4,
        "intrinsic_priority_rank": 2,
        "intrinsic_priority_score": 221,
    },
    "m3e_03": {
        "difficulty_rank": 10,
        "difficulty_score": 364,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 5,
        "intrinsic_priority_score": 228,
    },
    "m3e_04": {
        "difficulty_rank": 9,
        "difficulty_score": 354,
        "difficulty_tier": 4,
        "intrinsic_priority_rank": 3,
        "intrinsic_priority_score": 221,
    },
    "m3e_05": {
        "difficulty_rank": 15,
        "difficulty_score": 394,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 11,
        "intrinsic_priority_score": 246,
    },
    "m3e_06": {
        "difficulty_rank": 13,
        "difficulty_score": 384,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 9,
        "intrinsic_priority_score": 240,
    },
    "m3e_07": {
        "difficulty_rank": 11,
        "difficulty_score": 377,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 7,
        "intrinsic_priority_score": 236,
    },
    "m3e_08": {
        "difficulty_rank": 18,
        "difficulty_score": 404,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 14,
        "intrinsic_priority_score": 252,
    },
    "m3e_09": {
        "difficulty_rank": 12,
        "difficulty_score": 381,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 8,
        "intrinsic_priority_score": 238,
    },
    "m3e_11": {
        "difficulty_rank": 16,
        "difficulty_score": 394,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 12,
        "intrinsic_priority_score": 246,
    },
    "m3e_12": {
        "difficulty_rank": 17,
        "difficulty_score": 394,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 13,
        "intrinsic_priority_score": 246,
    },
    "m3e_13": {
        "difficulty_rank": 14,
        "difficulty_score": 384,
        "difficulty_tier": 5,
        "intrinsic_priority_rank": 10,
        "intrinsic_priority_score": 240,
    },
}

EXPECTED_PATTERN_IDS: tuple[str, ...] = tuple(EXPECTED_PATTERN_METRICS)

EXPECTED_DIFFICULTY_RANK_ORDER: tuple[str, ...] = tuple(
    sorted(
        EXPECTED_PATTERN_METRICS,
        key=lambda pid: EXPECTED_PATTERN_METRICS[pid]["difficulty_rank"],
    )
)

EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER: tuple[str, ...] = tuple(
    sorted(
        EXPECTED_PATTERN_METRICS,
        key=lambda pid: EXPECTED_PATTERN_METRICS[pid]["intrinsic_priority_rank"],
    )
)

# Audit md lists m3e_10 as a parent-R variant of m3e_09 (same equivalence class).
AUDIT_ONLY_PATTERN_IDS: frozenset[str] = frozenset({"m3e_10"})

EXPECTED_MINER_SEED_GENE_KEYS: tuple[str, ...] = tuple(
    f"miner_seed_{pattern_id}" for pattern_id in EXPECTED_PATTERN_IDS
)

# Back-compat alias (18 canonical keys after m3e_10 collapse).
EXPECTED_19_GENE_KEYS: tuple[str, ...] = EXPECTED_MINER_SEED_GENE_KEYS

MINER_SEED_SCHEMAS_PURGEABLE: frozenset[str] = frozenset({MINER_SEED_SCHEMA, MINER_SEED_SCHEMA_V2})


def metrics_for_pattern_id(pattern_id: str) -> PatternMetrics:
    """Return canonical difficulty/priority metrics for ``pattern_id``."""

    metrics = EXPECTED_PATTERN_METRICS.get(pattern_id)
    if metrics is None:
        msg = f"unknown miner seed pattern_id: {pattern_id!r}"
        raise ValueError(msg)
    return metrics


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
    "EXPECTED_PATTERN_METRICS",
    "EXHAUSTIVE_GENERATOR_STALE",
    "LAYOUT_TYPE_SHAPE_TO_FLUID",
    "MINER_LAYOUT_TYPES_SHAPE",
    "MINER_SEED_SCHEMA",
    "MINER_SEED_SCHEMA_V2",
    "MINER_SEED_SCHEMAS_PURGEABLE",
    "PatternMetrics",
    "gene_key_for_pattern_id",
    "gene_key_for_rank",
    "metrics_for_pattern_id",
]
