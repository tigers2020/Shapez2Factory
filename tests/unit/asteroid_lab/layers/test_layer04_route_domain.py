"""Layer 04 route search domain (PR-L4-2)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (  # noqa: E501
    L4_CELL_WEIGHT,
    build_l4_route_search_domain,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


def test_void_cost_is_one() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
    )
    void_coord = next(iter(cm.external_void_cells))
    assert domain.step_cost(void_coord) == L4_CELL_WEIGHT["void"]


def test_field_cost_is_five() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
    )
    field_coord = next(iter(cm.field_cells))
    assert domain.step_cost(field_coord) == L4_CELL_WEIGHT["asteroid_field"]


def test_miner_cell_cost_is_twenty() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    miner = next(iter(cm.field_cells))
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset({miner}),
        extension_cells=frozenset(),
    )
    assert domain.step_cost(miner) == L4_CELL_WEIGHT["m"]


def test_extension_cell_cost_is_ten() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    ext = next(iter(cm.field_cells))
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset({ext}),
    )
    assert domain.step_cost(ext) == L4_CELL_WEIGHT["e"]


def test_out_of_walkable_returns_none() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    domain = build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
    )
    assert domain.step_cost((999, 999)) is None
