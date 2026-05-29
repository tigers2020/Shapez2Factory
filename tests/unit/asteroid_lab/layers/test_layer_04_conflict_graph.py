"""Layer 04 v2 conflict graph."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.conflict_graph import (
    build_conflict_components,
    occupied_cells_for_entry,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_occupied_cells_includes_transport_stub() -> None:
    entry = succeeded_probe_at(
        (1, 1),
        mining=frozenset({(1, 1)}),
        transport=frozenset({(2, 1)}),
    )
    assert (2, 1) in occupied_cells_for_entry(entry)


def test_shared_stub_creates_single_component() -> None:
    e1 = succeeded_probe_at((1, 1), equivalence_key="e1", transport=frozenset({(9, 9)}))
    e2 = succeeded_probe_at((5, 5), equivalence_key="e2", transport=frozenset({(9, 9)}))
    components = build_conflict_components((e1, e2))
    assert len(components) == 1
    assert components[0].node_count == 2
    assert components[0].component_id == "component_0000"


def test_disjoint_entries_form_separate_components() -> None:
    e1 = succeeded_probe_at((0, 0), equivalence_key="e1", mining=frozenset({(0, 0)}))
    e2 = succeeded_probe_at((20, 20), equivalence_key="e2", mining=frozenset({(20, 20)}))
    components = build_conflict_components((e1, e2))
    assert len(components) == 2
    assert components[0].component_id == "component_0000"
    assert components[1].component_id == "component_0001"


def test_component_sort_key_uses_min_anchor_then_candidate_id() -> None:
    far = succeeded_probe_at((10, 10), equivalence_key="far", mining=frozenset({(10, 10)}))
    near = succeeded_probe_at((1, 2), equivalence_key="near", mining=frozenset({(1, 2)}))
    components = build_conflict_components((far, near))
    assert components[0].component_sort_key[0:2] == (2, 1)
    assert components[1].component_sort_key[0:2] == (10, 10)
