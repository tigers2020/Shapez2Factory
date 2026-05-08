"""Reachability gate vs rotated shape-miner output cell."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.reachability import (
    cheap_transport_escape_exists,
    pipe_step_allowed,
    transport_step_allowed,
)
from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    shape_miner_extension_positions,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.services.asteroid_reconstruction import (
    AsteroidReconstruction,
    reconstruct_from_decoded,
)


def test_output_skips_missing_x0_column() -> None:
    assert shape_miner_output_cell((-1, 0), 0) == (1, 0)
    assert shape_miner_extension_positions((2, 0), 0, 2) == ((1, 0), (-1, 0))


def test_cheap_false_when_output_head_inside_blocked_cluster_cells() -> None:
    """Belt head must not overlap extractor/extension footprint."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    rec = reconstruct_from_decoded(decoded)
    assert rec is not None
    assert not cheap_transport_escape_exists(
        rec=rec,
        extractor_core=(1, 0),
        rotation=0,
        cluster_cells=frozenset({(1, 0), (2, 0)}),
        routed_transport_cells=frozenset(),
        additional_blocked_cells=frozenset(),
    )


def test_cheap_true_r0_void_output_west_extension_chain() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    rec = reconstruct_from_decoded(decoded)
    assert rec is not None
    assert cheap_transport_escape_exists(
        rec=rec,
        extractor_core=(2, 0),
        rotation=0,
        cluster_cells=frozenset({(2, 0), (1, 0)}),
        routed_transport_cells=frozenset(),
        additional_blocked_cells=frozenset(),
    )


def test_escape_allows_step_into_soft_routed_cell_for_belt_and_pipe() -> None:
    """Routed transport is a soft reusable trunk, not a hard routing barrier."""

    rec = AsteroidReconstruction(
        blueprint_occupied_cells=frozenset({(10, 0)}),
        extraction_shell_cells=frozenset({(10, 0)}),
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=frozenset({(10, 0)}),
        x_min=1,
        x_max=12,
        y_min=0,
        y_max=0,
    )
    corridor = {(x, 0) for x in range(-5, 10)}
    pad_x0, pad_x1 = rec.x_min - 20, rec.x_max + 20
    pad_y0, pad_y1 = rec.y_min - 2, rec.y_max + 2
    slab = {(x, y) for x in range(pad_x0, pad_x1 + 1) for y in range(pad_y0, pad_y1 + 1)}
    additional_blocked = frozenset(slab - corridor - {(10, 0)})
    routed = frozenset({(8, 0)})
    assert cheap_transport_escape_exists(
        rec=rec,
        extractor_core=(10, 0),
        rotation=2,
        cluster_cells=frozenset({(10, 0)}),
        routed_transport_cells=routed,
        additional_blocked_cells=additional_blocked,
        transport_kind="belt",
    )
    assert cheap_transport_escape_exists(
        rec=rec,
        extractor_core=(10, 0),
        rotation=2,
        cluster_cells=frozenset({(10, 0)}),
        routed_transport_cells=routed,
        additional_blocked_cells=additional_blocked,
        transport_kind="pipe",
    )


def test_belt_and_pipe_step_allow_soft_routed_cells() -> None:
    blocked = frozenset({(0, 0)})
    nxy = (1, 1)
    assert pipe_step_allowed(nxy, blocked_cells=blocked)
    assert transport_step_allowed(
        (0, 1),
        nxy,
        blocked_cells=blocked,
        routed_transport_cells=frozenset({nxy}),
        directed_edges=frozenset(),
    )


def test_transport_step_reverse_edge_forbidden() -> None:
    cur = (1, 0)
    nxy = (2, 0)
    blocked: frozenset[tuple[int, int]] = frozenset()
    routed = frozenset({(1, 0), (2, 0)})
    edges = frozenset({(nxy, cur)})
    assert not transport_step_allowed(
        cur,
        nxy,
        blocked_cells=blocked,
        routed_transport_cells=routed,
        directed_edges=edges,
    )


def test_transport_step_trunk_reuse_allowed() -> None:
    cur = (1, 0)
    nxy = (2, 0)
    blocked = frozenset()
    routed = frozenset({(1, 0), (2, 0)})
    edges = frozenset({(cur, nxy)})
    assert transport_step_allowed(
        cur,
        nxy,
        blocked_cells=blocked,
        routed_transport_cells=routed,
        directed_edges=edges,
    )


def test_transport_step_entering_routed_cell_allowed() -> None:
    cur = (1, 0)
    nxy = (2, 0)
    assert transport_step_allowed(
        cur,
        nxy,
        blocked_cells=frozenset(),
        routed_transport_cells=frozenset({nxy}),
        directed_edges=frozenset(),
    )


def test_pipe_cheap_escape_true_when_output_on_solver_pipe_network() -> None:
    """이전 패스 파이프 트렁크에 붙이면 외곽까지 길을 찾지 않아도 탈출로 본다."""

    mineable = frozenset({(5, 0), (7, 0)})
    network = frozenset({(6, 0)})
    rec = AsteroidReconstruction(
        blueprint_occupied_cells=mineable,
        extraction_shell_cells=mineable,
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=mineable,
        x_min=5,
        x_max=7,
        y_min=0,
        y_max=0,
        solver_pipe_network_cells=network,
    )
    assert shape_miner_output_cell((5, 0), 0) == (6, 0)
    assert cheap_transport_escape_exists(
        rec=rec,
        extractor_core=(5, 0),
        rotation=0,
        cluster_cells=frozenset({(5, 0)}),
        routed_transport_cells=frozenset(),
        additional_blocked_cells=frozenset(),
        transport_kind="pipe",
    )


def test_rec_clone_merges_transport_hard_blocks() -> None:
    mineable = frozenset({(5, 0)})
    rec = AsteroidReconstruction(
        blueprint_occupied_cells=mineable,
        extraction_shell_cells=mineable,
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=mineable,
        x_min=5,
        x_max=5,
        y_min=0,
        y_max=0,
        transport_hard_block_cells=frozenset({(1, 1)}),
    )
    extra = frozenset({(9, 9)})
    out = AsteroidReconstruction(
        blueprint_occupied_cells=rec.blueprint_occupied_cells,
        extraction_shell_cells=rec.extraction_shell_cells,
        belt_cells=rec.belt_cells,
        pipe_cells=rec.pipe_cells,
        legacy_transport_cells=rec.legacy_transport_cells,
        interior_patch_cells=rec.interior_patch_cells,
        mineable_placement_cells=mineable,
        x_min=rec.x_min,
        x_max=rec.x_max,
        y_min=rec.y_min,
        y_max=rec.y_max,
        transport_hard_block_cells=frozenset(rec.transport_hard_block_cells | extra),
        solver_pipe_network_cells=rec.solver_pipe_network_cells,
    )
    assert out.mineable_placement_cells == mineable
    assert (1, 1) in out.transport_hard_block_cells
    assert (9, 9) in out.transport_hard_block_cells
