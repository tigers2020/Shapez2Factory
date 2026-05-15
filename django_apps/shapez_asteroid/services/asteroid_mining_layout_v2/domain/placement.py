"""STEP 2–3 placement DTOs (Pass1/Pass2) — pure domain; no I/O, Django, preview."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NewType

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.orchestration import (
    SolverRunContext,
)

PlacementId = NewType("PlacementId", str)


@dataclass(frozen=True, slots=True)
class OutputStub:
    """Adjacent cell in the extractor **output** direction (§3.1).

    Used for cheap-escape probe and routing anchor semantics; **not** the physical
    miner body tile. Pass1 preview must not materialize this cell as an installed
    extractor in ``mining_map`` committed frames (see ``PlacementBundle``).
    """

    extractor_placement_id: PlacementId
    cell: BlueprintCell
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class ExtractorPlacement:
    placement_id: PlacementId
    cell: BlueprintCell
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class ExtensionPlacement:
    placement_id: PlacementId
    anchor_extractor_id: PlacementId
    cell: BlueprintCell
    parent_cell: BlueprintCell
    #: Unit cardinal vector from ``cell`` toward ``parent_cell`` (extension "faces" parent, §3.3).
    orientation_toward_parent: tuple[int, int]


@dataclass(frozen=True, slots=True)
class PlacementBundle:
    """One Pass1/Pass2 head + extensions + output stub.

    ``extractor.cell`` is the physical miner coordinate (mineable). ``output_stub.cell``
    is the neighbouring output/probe coordinate only; it is not a second installed tile.
    """

    extractor: ExtractorPlacement
    extensions: tuple[ExtensionPlacement, ...]
    output_stub: OutputStub


@dataclass(frozen=True, slots=True)
class Pass1Result:
    """STEP 2 Pass1 (§7).

    ``placement_occupied_cells`` — extractor ∪ extension footprints (installed equipment).
    ``output_stub_cells`` — reserved belt/pipe anchor per bundle (not a second miner tile;
    Pass2 must not place equipment here; STEP 4 connects transport from these cells).
    ``occupied_cells`` — sorted ``placement_occupied_cells ∪ output_stub_cells`` for any
    caller that still expects a single Pass2 blocking set (§7.3).
    """

    placements: tuple[PlacementBundle, ...] = ()
    placement_occupied_cells: tuple[BlueprintCell, ...] = ()
    output_stub_cells: tuple[BlueprintCell, ...] = ()
    occupied_cells: tuple[BlueprintCell, ...] = ()
    placement_commit_entries: tuple[tuple[str, PlacementCommitState], ...] = ()
    beam_trace: tuple[dict[str, Any], ...] | None = None


@dataclass(frozen=True, slots=True)
class Pass2Result:
    """STEP 3 Pass2 provisional placements (§8)."""

    provisional_placements: tuple[PlacementBundle, ...] = ()
    blocked_cells_delta: tuple[BlueprintCell, ...] = ()
    placement_commit_entries: tuple[tuple[str, PlacementCommitState], ...] = ()
    beam_trace: tuple[dict[str, Any], ...] | None = None
    corridor_opening_trace: tuple[dict[str, object], ...] = ()
    pass1_after_corridor_gate: Pass1Result | None = None
    solver_ctx_after_corridor_gate: SolverRunContext | None = None


__all__ = [
    "ExtensionPlacement",
    "ExtractorPlacement",
    "OutputStub",
    "Pass1Result",
    "Pass2Result",
    "PlacementBundle",
    "PlacementId",
]
