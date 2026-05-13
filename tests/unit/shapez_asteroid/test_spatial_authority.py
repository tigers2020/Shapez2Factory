"""Spatial authority helpers (scratch vs mining_map consistency)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.spatial_authority import (  # noqa: E501
    assert_protected_corridors_agree_with_transport_map,
    assert_scratch_transport_subset_of_map,
    authority_note_for_phase,
    infer_transport_kind_from_mining_map,
    transport_coords_from_mining_map,
)


def test_authority_note_unknown_phase() -> None:
    assert "unknown" in authority_note_for_phase("no_such_phase").lower()


def test_transport_coords_from_mining_map_shape_belt() -> None:
    m = [
        {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        {"x": 2, "y": 0, "role": "pipe", "surface": "fluid"},
    ]
    assert transport_coords_from_mining_map(m, transport_kind="shape_belt") == {(1, 0)}


def test_assert_scratch_transport_subset_of_map_ok() -> None:
    st = Pass12LayoutScratch(transport_kind="shape_belt")
    st.transport_cells = {(1, 0)}
    m = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    assert_scratch_transport_subset_of_map(st, m, context="test")


def test_assert_scratch_transport_subset_of_map_raises() -> None:
    st = Pass12LayoutScratch(transport_kind="shape_belt")
    st.transport_cells = {(9, 9)}
    m = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    with pytest.raises(ValueError, match="scratch transport not on map"):
        assert_scratch_transport_subset_of_map(st, m)


def test_assert_scratch_transport_subset_materialized_only_allows_orphan_scratch() -> None:
    """Narrow Pass12 merge: scratch may list orphan coords; only materialized subset must map."""

    st = Pass12LayoutScratch(transport_kind="shape_belt")
    st.transport_cells = {(1, 0), (99, 99)}
    m = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    assert_scratch_transport_subset_of_map(
        st, m, materialized_scratch_transport=frozenset({(1, 0)})
    )


def test_infer_transport_kind_from_mining_map() -> None:
    assert (
        infer_transport_kind_from_mining_map([{"x": 1, "y": 0, "role": "pipe", "surface": "fluid"}])
        == "fluid_pipe"
    )
    assert (
        infer_transport_kind_from_mining_map([{"x": 1, "y": 0, "role": "belt", "surface": "shape"}])
        == "shape_belt"
    )
    assert infer_transport_kind_from_mining_map([]) == "shape_belt"


def test_assert_protected_corridors_agree_with_transport_map_ok() -> None:
    rs = {"hard_protected_corridors": [[1, 0]], "soft_protected_corridors": [[2, 0]]}
    m = [
        {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        {"x": 2, "y": 0, "role": "belt", "surface": "shape"},
    ]
    assert_protected_corridors_agree_with_transport_map(
        rs, m, transport_kind="shape_belt", context="test"
    )


def test_assert_protected_corridors_agree_with_transport_map_raises() -> None:
    rs = {"hard_protected_corridors": [[9, 9]]}
    m = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    with pytest.raises(ValueError, match="protected corridor not on map"):
        assert_protected_corridors_agree_with_transport_map(rs, m, transport_kind="shape_belt")
