"""
Pass1 / Pass2 bundle candidate models and shared placement geometry (§7–§8).

No route geometry; no ``final_route_cells`` (STEP 4 only).

**Deterministic direction ring**: ``CARDINAL_DIRS`` is **12 o'clock (north) first**, then
**clockwise** — ``(0, -1), (1, 0), (0, 1), (-1, 0)`` in ``(dx, dy)`` blueprint space
(``x`` east, ``y`` south).
"""

from __future__ import annotations

from collections import deque
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

# 12 o'clock = north = smaller Y, then clockwise N → E → S → W.
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
    """The three cardinal sides **excluding** extractor output, in clockwise order.

    Starting at the clockwise-next direction after ``out_dir`` on the N-E-S-W ring.
    """

    idx = CARDINAL_DIRS.index(out_dir)
    return tuple(CARDINAL_DIRS[(idx + k) % 4] for k in (1, 2, 3))


def orientation_toward_parent(child: BlueprintCell, parent: BlueprintCell) -> tuple[int, int]:
    """Unit vector from ``child`` toward ``parent`` (extension faces parent, §3.3)."""

    d = (parent[0] - child[0], parent[1] - child[1])
    if d not in CARDINAL_DIRS:
        msg = f"non-adjacent extension/parent pair: child={child!r} parent={parent!r}"
        raise ValueError(msg)
    return d


def grow_extension_cells(
    extractor: BlueprintCell,
    out_dir: tuple[int, int],
    stub: BlueprintCell,
    mineable: frozenset[BlueprintCell],
    used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> tuple[tuple[BlueprintCell, BlueprintCell, tuple[int, int]], ...]:
    """Up to 3 extensions: ``(ext_cell, parent_cell, orientation_toward_parent)``.

    Phase A — three extractor-adjacent slots (output excluded), clockwise from the slot
    immediately clockwise of ``out_dir``.

    Phase B — BFS from each placed extension: try ``CARDINAL_DIRS`` in order, skip step
    back onto ``parent``, attach up to global limit 3. Supports chains and same-level
    branching (multiple children of one extension when space allows).
    """

    out: list[tuple[BlueprintCell, BlueprintCell, tuple[int, int]]] = []
    local_used = set(used)

    def can_place(cell: BlueprintCell) -> bool:
        if cell[0] <= 0 or cell in local_used:
            return False
        if cell in (stub, extractor):
            return False
        if cell not in mineable:
            return False
        return not blocked_by_building(cell, transport_kind, reconstruction)

    for d in side_directions_after_output(out_dir):
        if len(out) >= 3:
            break
        nc = step_cell(extractor, d)
        if can_place(nc):
            out.append((nc, extractor, orientation_toward_parent(nc, extractor)))
            local_used.add(nc)

    q: deque[tuple[BlueprintCell, BlueprintCell]] = deque((ec, ep) for ec, ep, _ in out)

    while q and len(out) < 3:
        ext_cell, par = q.popleft()
        for d in CARDINAL_DIRS:
            if len(out) >= 3:
                break
            nxt = step_cell(ext_cell, d)
            if nxt == par:
                continue
            if can_place(nxt):
                out.append((nxt, ext_cell, orientation_toward_parent(nxt, ext_cell)))
                local_used.add(nxt)
                q.append((nxt, ext_cell))

    return tuple(out)


@dataclass(frozen=True, slots=True)
class Pass1BundleCandidate:
    """One outer-first placement candidate (probe-only escape; not a final route)."""

    candidate_id: str
    scan_index: int
    extractor_cell: BlueprintCell
    output_direction: tuple[int, int]
    output_stub_cell: BlueprintCell
    extension_cells: tuple[tuple[BlueprintCell, BlueprintCell, tuple[int, int]], ...]
    transport_kind: TransportKind
    score: float
    reject_reason: str | None = None
    placement_pass: Literal["pass1"] = "pass1"


@dataclass(frozen=True, slots=True)
class Pass2BundleCandidate:
    """One internal-fill candidate (§8); escape probe only — not occupied as a route."""

    candidate_id: str
    scan_index: int
    extractor_cell: BlueprintCell
    output_direction: tuple[int, int]
    output_stub_cell: BlueprintCell
    extension_cells: tuple[tuple[BlueprintCell, BlueprintCell, tuple[int, int]], ...]
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
    "orientation_toward_parent",
    "side_directions_after_output",
    "step_cell",
]
