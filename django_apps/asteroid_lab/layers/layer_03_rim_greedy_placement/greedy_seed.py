"""Minimal miner seed descriptor for rim greedy pass1 (v0)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GreedyMinerSeed:
    seed_id: str
    intrinsic_priority_rank: int
    miner_count: int = 1
    extension_count: int = 1


def sort_seeds_by_priority(seeds: tuple[GreedyMinerSeed, ...]) -> tuple[GreedyMinerSeed, ...]:
    return tuple(
        sorted(
            seeds,
            key=lambda s: (
                -s.intrinsic_priority_rank,
                -s.miner_count,
                -s.extension_count,
                s.seed_id,
            ),
        )
    )


# m3e_01 (miner + 3 extensions) is the highest-yield canonical bundle. Shorter rims
# degrade in-layout (extension_count 3 -> 2 -> 1), so no separately-named fallback seed
# is required; see layer_03_rim_greedy_placement.seed_orient.layout_seed_at_anchor.
DEFAULT_GREEDY_SEEDS: tuple[GreedyMinerSeed, ...] = (
    GreedyMinerSeed("m3e_01", intrinsic_priority_rank=1, miner_count=1, extension_count=3),
)


__all__ = ["DEFAULT_GREEDY_SEEDS", "GreedyMinerSeed", "sort_seeds_by_priority"]
