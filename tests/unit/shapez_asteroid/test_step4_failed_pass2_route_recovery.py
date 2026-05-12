"""STEP4 bounded Pass2 route recovery (one recovery session per failed provisional route)."""

from __future__ import annotations

from collections.abc import Callable

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
)


def _trapped_east_stub_fixture() -> tuple[
    list[dict],
    list[dict],
    Callable[[Coord], bool],
]:
    """East stub is a dead end; west stub (``r=2``) opens a corridor to external above (8,10)."""

    surface = "shape"
    rows: list[dict] = []

    def is_external(c: Coord) -> bool:
        return c == (8, 9)

    for x in range(8, 19):
        rows.append(
            {
                "x": x,
                "y": 10,
                "role": "inferred",
                "layout_kind": "asteroid_field",
                "surface": surface,
            }
        )

    rows.append(
        {
            "x": 15,
            "y": 10,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 0,
            "placement_id": "p2-000001",
        }
    )
    for belt_x in (16, 14):
        rows.append(
            {
                "x": belt_x,
                "y": 10,
                "role": "belt",
                "surface": surface,
                "placement_id": "p2-000001",
            }
        )
    for bx, by in ((17, 10), (16, 9), (16, 11)):
        rows.append({"x": bx, "y": by, "role": "pipe", "surface": "fluid"})

    final_rows = [dict(r) for r in rows]
    return rows, final_rows, is_external


def test_pass2_route_recovery_output_rotation() -> None:
    """Primary stub cannot move; recovery uses legal output rotation and confirms the route."""

    rows, final_rows, is_external = _trapped_east_stub_fixture()
    pr: dict[str, PlacementCommitRecord] = {
        "p2-000001": PlacementCommitRecord(
            placement_id="p2-000001",
            placement_pass="pass2",
            extractor_cell=(15, 10),
            extension_cells=(),
            stub_cell=(16, 10),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        )
    }
    r = run_step4_merge_aware_routing(
        rows,
        final_mining_map=final_rows,
        is_external=is_external,
        placement_records=pr,
    )
    tl = r.trunk_load
    assert tl.get("step4_failed_route_recovery_attempted_count") == 1
    assert tl.get("step4_failed_route_recovery_success_count") == 1
    assert tl.get("step4_failed_route_recovery_rejected_count") == 0
    assert tl.get("recovery_search_mode") == "output_rotation"
    assert not r.rolled_back_placement_ids
    cells = {(row["x"], row["y"]): row for row in r.map_after_routing}
    assert cells[(15, 10)].get("r") == 2
    assert any(rt.placement_id == "p2-000001" and len(rt.path) > 1 for rt in r.routes)
