"""Patch C: placement FSM map stamp + P2-C rollback orphan transport strip (§9.6)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_p2c_corrective as p2c,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rollback_exclusive_transport_path_cells,
    rollback_placement_cells,
    stamp_placement_commit_on_map_rows,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as fv,
)


def test_rollback_exclusive_transport_path_clears_orphan_belt() -> None:
    """P2-C: belt cells unique to a rolled route path are removed or restored."""

    path = ((6, 5), (7, 5), (8, 5))
    mineable = frozenset({(6, 5), (7, 5), (8, 5)})
    final_cells = {
        (6, 5): {"x": 6, "y": 5, "role": "inferred", "layout_kind": "asteroid_field"},
        (7, 5): {"x": 7, "y": 5, "role": "inferred", "layout_kind": "asteroid_field"},
        (8, 5): {"x": 8, "y": 5, "role": "inferred", "layout_kind": "asteroid_field"},
    }
    cells = {
        (6, 5): {"x": 6, "y": 5, "role": "belt", "surface": "shape"},
        (7, 5): {"x": 7, "y": 5, "role": "belt", "surface": "shape"},
        (8, 5): {"x": 8, "y": 5, "role": "belt", "surface": "shape"},
    }
    rollback_exclusive_transport_path_cells(
        cells,
        route_path=path,
        want_role="belt",
        preserve_coords=frozenset(),
        final_cells=final_cells,
        mineable=mineable,
    )
    assert cells[(6, 5)] == final_cells[(6, 5)]
    assert cells[(7, 5)] == final_cells[(7, 5)]
    assert cells[(8, 5)] == final_cells[(8, 5)]


def test_rollback_exclusive_transport_preserves_shared_trunk_cell() -> None:
    """Cells in ``preserve_coords`` keep their belt row even when on this route's path."""

    path = ((7, 5), (8, 5))
    mineable = frozenset({(7, 5), (8, 5)})
    final_cells = {
        (7, 5): {"x": 7, "y": 5, "role": "inferred", "layout_kind": "asteroid_field"},
        (8, 5): {"x": 8, "y": 5, "role": "inferred", "layout_kind": "asteroid_field"},
    }
    shared = {"x": 8, "y": 5, "role": "belt", "surface": "shape", "shared_trunk": True}
    cells = {
        (7, 5): {"x": 7, "y": 5, "role": "belt", "surface": "shape"},
        (8, 5): dict(shared),
    }
    rollback_exclusive_transport_path_cells(
        cells,
        route_path=path,
        want_role="belt",
        preserve_coords=frozenset({(8, 5)}),
        final_cells=final_cells,
        mineable=mineable,
    )
    assert cells[(7, 5)] == final_cells[(7, 5)]
    assert cells[(8, 5)] == shared


def test_stamp_placement_commit_syncs_placement_state_for_step9() -> None:
    """Row-level ``placement_state`` must match ``placement_commit_state`` after stamp (§9.6)."""

    pid = "p2-000099"
    cells: dict[tuple[int, int], dict[str, Any]] = {
        (5, 5): {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "miner",
            "placement_id": pid,
            "placement_state": "provisional_placed",
        }
    }
    rec = PlacementCommitRecord(
        placement_id=pid,
        placement_pass="pass2",
        extractor_cell=(5, 5),
        extension_cells=(),
        stub_cell=(6, 5),
        transport_kind="shape_belt",
        state=PlacementCommitState.QUARANTINED_UNROUTED,
        rollback_reason="no_route",
    )
    stamp_placement_commit_on_map_rows(cells, {pid: rec})
    row = cells[(5, 5)]
    assert row["placement_commit_state"] == PlacementCommitState.QUARANTINED_UNROUTED.value
    assert row["placement_state"] == PlacementCommitState.QUARANTINED_UNROUTED.value


def test_final_validation_rejects_unfinalized_placement_rows() -> None:
    """§15: geometry gate fails when provisional / quarantined FSM markers remain on the map."""

    mining_map: list[dict[str, Any]] = [
        {
            "x": 3,
            "y": 3,
            "role": "belt",
            "surface": "shape",
            "placement_commit_state": "provisional_placed",
        },
    ]
    rep = fv.validate_final_mining_layout(mining_map)
    assert rep.provisional_placed_row_count == 1
    assert rep.geometry_valid is False


def test_rollback_cleanup_bundle_plus_no_duplicate_strip() -> None:
    """``rollback_placement_cells`` + exclusive path strip is idempotent on bundle coords."""

    ext = (10, 10)
    stub = (11, 10)
    mineable = frozenset({ext, stub, (12, 10)})
    final_cells = {
        ext: {"x": 10, "y": 10, "role": "occupied", "layout_kind": "miner", "r": 0},
        stub: {"x": 11, "y": 10, "role": "inferred", "layout_kind": "asteroid_field"},
        (12, 10): {"x": 12, "y": 10, "role": "inferred", "layout_kind": "asteroid_field"},
    }
    cells = {
        ext: dict(final_cells[ext]),
        stub: {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
        (12, 10): {"x": 12, "y": 10, "role": "belt", "surface": "shape"},
    }
    rec = PlacementCommitRecord(
        placement_id="p2-000100",
        placement_pass="pass2",
        extractor_cell=ext,
        extension_cells=(),
        stub_cell=stub,
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id="route-p2-000100",
    )
    path = (stub, (12, 10))
    rollback_placement_cells(cells, rec, final_cells, mineable)
    rollback_exclusive_transport_path_cells(
        cells,
        route_path=path,
        want_role="belt",
        preserve_coords=frozenset(),
        final_cells=final_cells,
        mineable=mineable,
    )
    assert cells[ext] == final_cells[ext]
    assert cells[stub] == final_cells[stub]
    assert cells[(12, 10)] == final_cells[(12, 10)]


def test_p2c_cascade_rollback_strips_exclusive_route_transport() -> None:
    """§9.6 rule 7: ROUTED_CONFIRMED revalidation sees disconnect → cascade rollback strips path."""

    pid = "p2-000201"
    ext = (20, 20)
    stub = (21, 20)
    tail = (22, 20)
    mineable = frozenset({ext, stub, tail})
    final_cells = {
        ext: {"x": 20, "y": 20, "role": "occupied", "layout_kind": "miner", "r": 0},
        stub: {"x": 21, "y": 20, "role": "inferred", "layout_kind": "asteroid_field"},
        tail: {"x": 22, "y": 20, "role": "inferred", "layout_kind": "asteroid_field"},
    }
    cells: dict[tuple[int, int], dict[str, Any]] = {
        ext: dict(final_cells[ext]) | {"placement_id": pid},
        stub: {"x": 21, "y": 20, "role": "belt", "surface": "shape"},
        tail: {"x": 22, "y": 20, "role": "belt", "surface": "shape"},
    }
    rec = PlacementCommitRecord(
        placement_id=pid,
        placement_pass="pass2",
        extractor_cell=ext,
        extension_cells=(),
        stub_cell=stub,
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id=f"route-{pid}",
    )
    work_records = {pid: rec}
    routes_out = [
        Step4Route(
            extractor_cell=ext,
            stub_cell=stub,
            transport_kind="shape_belt",
            path=(stub, tail),
            merged_to_existing=False,
            reached_external=True,
            placement_id=pid,
        )
    ]
    failures: list[dict[str, Any]] = []
    trunk_edge_hits: dict[str, int] = {}

    with (
        patch.object(p2c, "_facade_stub_reaches_external_trunk", return_value=False),
        patch.object(p2c, "_facade_dijkstra", return_value=None),
    ):
        routes_out2, metrics = p2c.p2c_revalidate_and_correct(
            cells,
            routes_out,
            work_records,
            mineable=mineable,
            asteroid=frozenset(),
            final_cells=final_cells,
            is_external=lambda c: c[0] > 99,
            surface="shape",
            failures=failures,
            trunk_edge_hits=trunk_edge_hits,
        )

    assert metrics["cascade_rollback_count"] >= 1
    assert metrics["broken_routed_route_count"] >= 1
    assert routes_out2 == []
    assert work_records[pid].state == PlacementCommitState.ROLLED_BACK
    assert cells[stub].get("role") != "belt"
    assert cells[tail].get("role") != "belt"
