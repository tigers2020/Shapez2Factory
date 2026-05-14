"""
Pass1 / Pass2 bundle candidate models and shared placement geometry (§7–§8).

No route geometry; no ``final_route_cells`` (STEP 4 only).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)

# 12 o'clock = north = smaller Y (y-down grid), then clockwise N E S W.
CARDINAL_DIRS: tuple[tuple[int, int], ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


def step_cell(cell: BlueprintCell, d: tuple[int, int]) -> BlueprintCell:
    return (cell[0] + d[0], cell[1] + d[1])


def infer_transport_kind(reconstruction: ReconstructionDTO) -> TransportKind:
    has_belt = bool(reconstruction.belt_cells)
    has_pipe = bool(reconstruction.pipe_cells)
    if has_pipe and not has_belt:
        return TransportKind.FLUID_PIPE
    return TransportKind.SHAPE_BELT


def blocked_by_building(
    c: BlueprintCell,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> bool:
    if c not in reconstruction.full_barrier_cells:
        return False
    if transport_kind is TransportKind.SHAPE_BELT and c in frozenset(reconstruction.belt_cells):
        return False
    if transport_kind is TransportKind.FLUID_PIPE and c in frozenset(reconstruction.pipe_cells):
        return False
    return True


def side_directions_after_output(out_dir: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    idx = CARDINAL_DIRS.index(out_dir)
    return tuple(CARDINAL_DIRS[(idx + k) % 4] for k in (1, 2, 3))


def grow_extension_cells(
    extractor: BlueprintCell,
    out_dir: tuple[int, int],
    stub: BlueprintCell,
    mineable: frozenset[BlueprintCell],
    used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> tuple[tuple[BlueprintCell, BlueprintCell], ...]:
    """Up to 3 extensions; ``(ext_cell, parent_cell)``."""

    out: list[tuple[BlueprintCell, BlueprintCell]] = []

    def can_extension(cell: BlueprintCell) -> bool:
        if cell[0] <= 0 or cell in used or cell in (stub, extractor):
            return False
        if cell not in mineable:
            return False
        return not blocked_by_building(cell, transport_kind, reconstruction)

    for d in side_directions_after_output(out_dir):
        if len(out) >= 3:
            break
        nc = step_cell(extractor, d)
        if can_extension(nc):
            out.append((nc, extractor))
            used.add(nc)

    if len(out) < 3 and out:
        first_cell, _fp = out[0]
        par = extractor
        for d in CARDINAL_DIRS:
            nc = step_cell(first_cell, d)
            if nc in (par, stub, extractor):
                continue
            if can_extension(nc):
                out.append((nc, first_cell))
                used.add(nc)
                break

    return tuple(out)


@dataclass(frozen=True, slots=True)
class Pass1BundleCandidate:
    """One outer-first placement candidate (probe-only escape; not a final route)."""

    candidate_id: str
    extractor_cell: BlueprintCell
    output_direction: tuple[int, int]
    output_stub_cell: BlueprintCell
    extension_cells: tuple[tuple[BlueprintCell, BlueprintCell], ...]
    transport_kind: TransportKind
    score: float
    reject_reason: str | None = None
    placement_pass: Literal["pass1"] = "pass1"


@dataclass(frozen=True, slots=True)
class Pass2BundleCandidate:
    """One internal-fill candidate (§8); escape probe only — not occupied as a route."""

    candidate_id: str
    extractor_cell: BlueprintCell
    output_direction: tuple[int, int]
    output_stub_cell: BlueprintCell
    extension_cells: tuple[tuple[BlueprintCell, BlueprintCell], ...]
    transport_kind: TransportKind
    score: float
    reject_reason: str | None = None
    placement_pass: Literal["pass2"] = "pass2"


__all__ = [
    "CARDINAL_DIRS",
    "Pass1BundleCandidate",
    "Pass2BundleCandidate",
    "blocked_by_building",
    "grow_extension_cells",
    "infer_transport_kind",
    "side_directions_after_output",
    "step_cell",
]
