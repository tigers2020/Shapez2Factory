"""Sequence 3 — candidate generator + route probe integration."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import build_optimization_input
from django_apps.shapez_asteroid.optimization.bundle_candidate_generator import (
    generate_bundle_candidates,
)
from django_apps.shapez_asteroid.optimization.dto import CandidateGenerationConfig
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    TransportKind,
)
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    NoOpOptimizationReplayRecorder,
)
from django_apps.shapez_asteroid.optimization.pattern_library import build_pattern_library
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .test_optimization_input import _cell, _snapshot


def _greenfield_square_input():
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field", server_x=0, server_y=0),
        _cell(2, 1, cell_kind="asteroid_shape_field", server_x=1, server_y=0),
        _cell(1, 2, cell_kind="asteroid_shape_field", server_x=0, server_y=1),
        _cell(2, 2, cell_kind="asteroid_shape_field", server_x=1, server_y=1),
    )
    snap = _snapshot(cells)
    cleanup = deconstruct_snapshot(snap)
    recon = reconstruct_snapshot(snap)
    return build_optimization_input(recon, cleanup)


def test_integration_candidate_generator_invokes_route_probe_immediately() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    for c in res.normal_candidates:
        assert c.route_probe_result.path


def test_integration_same_input_same_pools() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=20,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    a = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    b = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert tuple(c.candidate_id for c in a.normal_candidates) == tuple(
        c.candidate_id for c in b.normal_candidates
    )
    assert len(a.rejected_candidates) == len(b.rejected_candidates)


def test_integration_route_domain_not_mutated() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    before = {k: domain[k].hard_blocked for k in list(domain.keys())[:5]}
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    after = {k: domain[k].hard_blocked for k in before}
    assert before == after


def test_integration_allow_diagnostic_unreachable_controls_unreachable_rejects() -> None:
    inp = replace(_greenfield_square_input(), route_goals=frozenset())
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    base = dict(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        max_candidates=None,
        route_probe_max_expansions=0,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    on = generate_bundle_candidates(
        inp,
        domain,
        build_pattern_library(),
        CandidateGenerationConfig(allow_diagnostic_unreachable=True, **base),
    )
    off = generate_bundle_candidates(
        inp,
        domain,
        build_pattern_library(),
        CandidateGenerationConfig(allow_diagnostic_unreachable=False, **base),
    )
    assert on.normal_candidates == () and off.normal_candidates == ()
    n_on = sum(
        1
        for r in on.rejected_candidates
        if r.rejection_reason is CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
    )
    n_off = sum(
        1
        for r in off.rejected_candidates
        if r.rejection_reason is CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
    )
    assert n_on > 0
    assert n_off == 0


def test_integration_replay_noop_recorder_identical_pools() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=20,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    patterns = build_pattern_library()
    base = generate_bundle_candidates(inp, domain, patterns, cfg)
    noop = NoOpOptimizationReplayRecorder()
    with_noop = generate_bundle_candidates(inp, domain, patterns, cfg, replay_recorder=noop)
    assert base.normal_candidates == with_noop.normal_candidates
    assert base.rejected_candidates == with_noop.rejected_candidates
    assert noop.frames == ()


def test_integration_topology_graph_and_route_domain_jointly_constrain() -> None:
    """Regression guard: probe consumes both graph adjacency and per-cell domain."""

    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    assert inp.topology_graph.edges
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert isinstance(res.normal_candidates, tuple)
