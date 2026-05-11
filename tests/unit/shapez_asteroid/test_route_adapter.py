"""P3-E2 route adapter contract (solver → lex router inputs)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_adapter import (
    RouteAdapterInput,
    build_route_adapter_output,
    route_adapter_input_for_pass3_stub,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    RouteZone,
    build_route_zone_map,
)


def test_build_route_adapter_output_bbox_and_blocked() -> None:
    ast = frozenset(
        (x, y) for x in (1, 2, 3) for y in (1, 2, 3)
    )  # 3×3 blob so center is true interior
    stub = (1, 0)
    anchor = (5, 0)
    inp = RouteAdapterInput(
        mining_map=(),
        asteroid_cells=ast,
        mineable_cells=frozenset({(2, 2)}),
        extractor_cells=frozenset({(10, 10)}),
        extension_cells=frozenset({(11, 11)}),
        final_route_cells=frozenset({stub, anchor}),
        fixed_output_stub=stub,
        transport_kind="shape_belt",
        existing_trunk_cells=frozenset({anchor}),
        external_goal_cells=frozenset({anchor}),
        hard_protected_cells=frozenset({(3, 3)}),
        soft_protected_cells=frozenset({(4, 4)}),
        bbox_margin=2,
    )
    out = build_route_adapter_output(inp)
    assert out.start_stub == stub
    assert out.goal_cells == frozenset({anchor})
    assert (10, 10) in out.blocked_cells
    assert (3, 3) in out.blocked_cells
    assert (4, 4) in out.protected_cells and (3, 3) in out.protected_cells
    assert stub in out.allowed_cells and anchor in out.allowed_cells
    assert out.zone_by_cell[(2, 2)] is RouteZone.FILLABLE_INTERIOR


def test_build_route_zone_map_splits_fillable_from_interior_void() -> None:
    """Full-interior rock vs same-topology mineable cell get distinct zones."""

    ast = frozenset((x, y) for x in range(1, 6) for y in range(1, 6))
    mineable = frozenset({(3, 3)})
    zm = build_route_zone_map(asteroid_cells=ast, mineable_cells=mineable)
    assert zm[(3, 3)] is RouteZone.FILLABLE_INTERIOR
    assert zm[(3, 2)] is RouteZone.ASTEROID_INTERIOR_VOID


def test_route_adapter_input_for_pass3_stub_collects_extractors() -> None:
    cells = {
        (1, 1): {"layout_kind": "miner", "role": "occupied"},
        (2, 1): {"layout_kind": "extension", "role": "occupied"},
        (1, 0): {"role": "belt"},
    }
    inp = route_adapter_input_for_pass3_stub(
        mining_map_rows=[],
        cells=cells,
        mineable_cells=frozenset(),
        asteroid_cells=frozenset({(1, 1)}),
        fixed_output_stub=(1, 0),
        anchor=(5, 0),
        transport_kind="shape_belt",
        same_kind_transport_cells=frozenset({(1, 0), (5, 0)}),
        trunk_cells=frozenset({(5, 0)}),
    )
    assert (1, 1) in inp.extractor_cells
    assert (2, 1) in inp.extension_cells
