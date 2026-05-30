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


DEFAULT_GREEDY_SEEDS: tuple[GreedyMinerSeed, ...] = (
    GreedyMinerSeed("rim_greedy_m1e1", intrinsic_priority_rank=1),
)


__all__ = ["DEFAULT_GREEDY_SEEDS", "GreedyMinerSeed", "sort_seeds_by_priority"]
