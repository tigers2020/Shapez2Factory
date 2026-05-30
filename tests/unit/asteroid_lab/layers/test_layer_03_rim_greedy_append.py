"""Layer 03 rim greedy append mapper (Task B)."""

from __future__ import annotations

import ast
from pathlib import Path

from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
from django_apps.asteroid_lab.layers.contracts.rim_greedy import CommittedRimSeedPlacement
from django_apps.asteroid_lab.layers.contracts.rim_greedy_append import (
    LAYER_03_APPEND_SOURCE,
    AppendCellKind,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.append import (
    append_committed_rim_placements,
    provisional_overlay_from_append,
)

_APPEND_MODULE = Path(
    __import__(
        "django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.append",
        fromlist=["append"],
    ).__file__
)


def _placement(
    *,
    placement_id: str = "rim_greedy_CW_TL_0",
    miner: frozenset[tuple[int, int]] = frozenset({(6, 4)}),
    extension: frozenset[tuple[int, int]] = frozenset({(5, 4)}),
    stub: tuple[int, int] = (7, 4),
    route: tuple[tuple[int, int], ...] = ((7, 4), (8, 4)),
) -> CommittedRimSeedPlacement:
    return CommittedRimSeedPlacement(
        placement_id=placement_id,
        variant_id="CW_TL",
        anchor=(6, 4),
        output_dir="E",
        seed_id="rim_greedy_m1e1",
        miner_cells=miner,
        extension_cells=extension,
        m_output_stub=stub,
        route_probe_path=route,
    )


def test_append_module_does_not_import_replay() -> None:
    tree = ast.parse(_APPEND_MODULE.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    replay_hits = [name for name in imports if "replay" in name]
    assert replay_hits == []


def test_append_committed_placement_cells() -> None:
    result = append_committed_rim_placements(committed_placements=(_placement(),))
    assert result.placement_count == 1
    assert result.source_layer == LAYER_03_APPEND_SOURCE
    kinds = {cell.kind for cell in result.cells}
    assert AppendCellKind.MINER in kinds
    assert AppendCellKind.EXTENSION in kinds
    assert AppendCellKind.OUTPUT_STUB in kinds
    assert AppendCellKind.ROUTE_RESERVED in kinds
    assert len(result.cells) >= 4
    assert result.route_reserved_cell_count >= 1


def test_stub_wins_over_route_on_same_coord() -> None:
    result = append_committed_rim_placements(
        committed_placements=(_placement(stub=(7, 4), route=((7, 4), (8, 4))),),
    )
    at_stub = [c for c in result.cells if c.coord == (7, 4)]
    assert len(at_stub) == 1
    assert at_stub[0].kind is AppendCellKind.OUTPUT_STUB


def test_append_empty_placements() -> None:
    result = append_committed_rim_placements(committed_placements=())
    assert result.placement_count == 0
    assert result.cells == ()
    assert result.route_reserved_cell_count == 0


def test_provisional_overlay_from_append_includes_route_cells() -> None:
    append_result = append_committed_rim_placements(committed_placements=(_placement(),))
    overlay = provisional_overlay_from_append(
        append_result,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert overlay.occupied_cells == frozenset(c.coord for c in append_result.cells)
    route_coords = {c.coord for c in append_result.cells if c.kind is AppendCellKind.ROUTE_RESERVED}
    assert route_coords
    assert route_coords <= overlay.occupied_cells
    for coord in route_coords:
        assert overlay.by_cell[coord].role is BundleCellRole.ROUTE_RESERVED


def test_append_deterministic_cell_order() -> None:
    placements = (
        _placement(),
        _placement(
            placement_id="rim_greedy_CW_TL_1",
            miner=frozenset({(6, 5)}),
            extension=frozenset({(6, 4)}),
            stub=(6, 6),
            route=((6, 6),),
        ),
    )
    first = append_committed_rim_placements(committed_placements=placements)
    second = append_committed_rim_placements(committed_placements=placements)
    assert first.cells == second.cells
    coords = [c.coord for c in first.cells]
    assert coords == sorted(coords)
