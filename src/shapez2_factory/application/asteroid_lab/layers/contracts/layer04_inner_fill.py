"""Layer 04 inner pattern fill contracts (stub)."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


@dataclass(frozen=True, slots=True)
class Layer04InnerFillResult:
    interior_occupied_cells: frozenset[Coord] = frozenset()

    @classmethod
    def empty(cls) -> Layer04InnerFillResult:
        return cls()


__all__ = ["Layer04InnerFillResult"]
