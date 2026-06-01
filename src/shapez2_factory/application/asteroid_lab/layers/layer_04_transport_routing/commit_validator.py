"""Commit-time overlap rules for Layer 04 transport tiles."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


@dataclass(frozen=True, slots=True)
class L4CommitValidator:
    equipment_cells: frozenset[Coord]
    connector_cells: frozenset[Coord]
    stub_cells: frozenset[Coord]

    def validate_route_cell(self, coord: Coord) -> Layer04FailureReason | None:
        if coord in self.connector_cells or coord in self.stub_cells:
            return None
        if coord in self.equipment_cells:
            return Layer04FailureReason.COMMIT_OVERLAP_BLOCKED
        return None

    def validate_path(self, path: tuple[Coord, ...]) -> Layer04FailureReason | None:
        for coord in path:
            reason = self.validate_route_cell(coord)
            if reason is not None:
                return reason
        return None


__all__ = ["L4CommitValidator"]
