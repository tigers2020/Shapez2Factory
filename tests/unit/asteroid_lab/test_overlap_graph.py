"""Unit tests for overlap graph packing bounds (P1-ELCP-RF-B1)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.selection.overlap_graph import (
    UpperBoundMethod,
    build_overlap_adjacency,
    compute_overlap_packing_bounds,
    compute_target_floor,
    exact_mis_size_for_component,
    greedy_coloring_upper_bound_for_component,
    heuristic_mis_for_component,
    phase0_is_no_go,
)


def _minimal_candidate(
    candidate_id: str,
    occupied: frozenset[Coord],
) -> BundleCandidate:
    anchor = next(iter(occupied))
    pattern = BundlePattern(
        pattern_id="test",
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir="east",
        fixed_output_transport_offset=(0, 0),
        output_stub_offset=(0, 0),
        throughput_factor=1,
        topology_kind="test",
    )
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=anchor,
        output_dir="east",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
    )


def test_build_overlap_adjacency_two_overlapping_candidates() -> None:
    a = _minimal_candidate("a", frozenset({(0, 0), (1, 0)}))
    b = _minimal_candidate("b", frozenset({(1, 0), (2, 0)}))
    c = _minimal_candidate("c", frozenset({(5, 5)}))
    adj = build_overlap_adjacency((a, b, c))
    assert "b" in adj["a"]
    assert "a" in adj["b"]
    assert adj["c"] == frozenset()


def test_exact_mis_size_path_graph_size_2() -> None:
    adj = {
        "a": frozenset({"b"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"b"}),
    }
    assert exact_mis_size_for_component(adj, ("a", "b", "c")) == 2


def test_heuristic_mis_triangle_is_one() -> None:
    adj = {
        "a": frozenset({"b", "c"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"a", "b"}),
    }
    assert heuristic_mis_for_component(adj, ("a", "b", "c")) == 1


def test_greedy_coloring_upper_bound_triangle_is_three() -> None:
    adj = {
        "a": frozenset({"b", "c"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"a", "b"}),
    }
    assert greedy_coloring_upper_bound_for_component(adj, ("a", "b", "c")) == 3


def test_compute_overlap_packing_bounds_disjoint_three() -> None:
    candidates = (
        _minimal_candidate("a", frozenset({(0, 0)})),
        _minimal_candidate("b", frozenset({(1, 0)})),
        _minimal_candidate("c", frozenset({(2, 0)})),
    )
    bounds = compute_overlap_packing_bounds(candidates, greedy_regret_baseline=1)
    assert bounds.vertex_count == 3
    assert bounds.edge_count == 0
    assert bounds.best_known_independent_set_size == 3
    assert bounds.upper_bound == 3
    assert bounds.upper_bound_method is UpperBoundMethod.COMPONENT_EXACT
    assert bounds.exact_mis_size == 3


def test_compute_target_floor_at_least_100_when_large_mis() -> None:
    assert compute_target_floor(200) == 100
    assert compute_target_floor(80) == 80


def test_phase0_is_no_go_when_mis_near_baseline() -> None:
    assert phase0_is_no_go(best_known_independent_set_size=62, greedy_regret_baseline=59)
    assert not phase0_is_no_go(best_known_independent_set_size=120, greedy_regret_baseline=59)
