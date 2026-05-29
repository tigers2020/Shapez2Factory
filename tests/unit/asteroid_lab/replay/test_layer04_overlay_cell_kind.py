"""L4 replay overlay kinds must use domain cell_kind, not observation aliases."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCellRole,
    BundlePlacement,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.replay.layer04_segment import _overlay_cells_for_placement


def _succeeded_entry(*, placements: tuple[BundlePlacement, ...]) -> RouteProbedBundleCandidate:
    anchor = (3, 4)
    mining = frozenset(p.coord for p in placements if p.cell_role is BundleCellRole.MINER)
    mining |= frozenset(
        p.coord for p in placements if p.cell_role is BundleCellRole.EXTENSION
    )
    stub = frozenset(
        p.coord for p in placements if p.cell_role is BundleCellRole.TRANSPORT_STUB
    )
    stub_start = min(stub) if stub else (4, 4)
    base = make_bundle_candidate_for_test(
        anchor_coord=anchor,
        output_dir=Direction.E,
        mining_occupied_cells=mining,
        transport_stub_cells=stub,
        route_probe_start_coord=stub_start,
    )
    candidate = replace(base, placements=placements)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=(8, 4),
            path_coords=(stub_start, (8, 4)),
            steps_expanded=2,
            transport_kind=TransportKind.SHAPE_BELT,
            route_cost=4,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )


def test_layer04_overlay_extractor_kind_is_domain_shape_miner() -> None:
    anchor = (3, 4)
    placements = (
        BundlePlacement(
            coord=anchor,
            layout_t="Layout_ShapeMiner",
            rotation=0,
            cell_role=BundleCellRole.MINER,
        ),
        BundlePlacement(
            coord=(4, 4),
            layout_t="SpaceBelt_Forward",
            rotation=0,
            cell_role=BundleCellRole.TRANSPORT_STUB,
        ),
    )
    placement = build_rim_bundle_placement(_succeeded_entry(placements=placements))
    cells = _overlay_cells_for_placement(placement)
    miner_rows = [c for c in cells if (c.x, c.y) == anchor]
    assert miner_rows
    assert miner_rows[0].kind == "shape_miner"
    assert miner_rows[0].kind != "miner"


def test_layer04_overlay_extension_kind_is_domain_shape_miner_extension() -> None:
    ext_coord = (2, 4)
    placements = (
        BundlePlacement(
            coord=(3, 4),
            layout_t="Layout_ShapeMiner",
            rotation=0,
            cell_role=BundleCellRole.MINER,
        ),
        BundlePlacement(
            coord=ext_coord,
            layout_t="Layout_ShapeMinerExtension",
            rotation=0,
            cell_role=BundleCellRole.EXTENSION,
        ),
        BundlePlacement(
            coord=(4, 4),
            layout_t="SpaceBelt_Forward",
            rotation=0,
            cell_role=BundleCellRole.TRANSPORT_STUB,
        ),
    )
    placement = build_rim_bundle_placement(_succeeded_entry(placements=placements))
    cells = _overlay_cells_for_placement(placement)
    ext_rows = [c for c in cells if (c.x, c.y) == ext_coord]
    assert ext_rows
    assert ext_rows[0].kind == "shape_miner_extension"
    assert ext_rows[0].kind != "extension"


def test_layer04_overlay_transport_stub_kind_is_domain_space_belt() -> None:
    stub = (4, 4)
    placements = (
        BundlePlacement(
            coord=(3, 4),
            layout_t="Layout_ShapeMiner",
            rotation=0,
            cell_role=BundleCellRole.MINER,
        ),
        BundlePlacement(
            coord=stub,
            layout_t="SpaceBelt_Forward",
            rotation=0,
            cell_role=BundleCellRole.TRANSPORT_STUB,
        ),
    )
    placement = build_rim_bundle_placement(_succeeded_entry(placements=placements))
    cells = _overlay_cells_for_placement(placement)
    stub_rows = [c for c in cells if (c.x, c.y) == stub]
    assert stub_rows
    assert stub_rows[0].kind == "space_belt"
    assert stub_rows[0].kind != "transport_stub"
