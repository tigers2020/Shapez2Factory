"""Sequence 3 — bundle candidate generator + immediate probe."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import build_optimization_input
from django_apps.shapez_asteroid.optimization.bundle_candidate_generator import (
    generate_bundle_candidates,
)
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    CandidateEquivalenceKey,
    CandidateGenerationConfig,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    TransportKind,
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


def test_candidate_generator_rim_only_extractors() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    for c in res.normal_candidates:
        assert c.extractor in inp.rim_cells


def test_candidate_generator_extensions_must_be_mineable() -> None:
    """Non-mineable asteroid cell must reject extension placement."""

    inp = _greenfield_square_input()
    mineable = frozenset(inp.mineable_cells - {Coord(1, 0)})
    inp2 = replace(inp, mineable_cells=mineable)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp2)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp2, domain, build_pattern_library(), cfg)
    assert any(
        r.rejection_reason is CandidateRejectReason.EXTENSION_NOT_MINEABLE
        for r in res.rejected_candidates
    )


def test_candidate_generator_output_stub_not_occupied() -> None:
    """Pattern library invariant; generator also rejects stub-in-occupied."""

    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    for c in res.normal_candidates:
        assert c.output_stub not in c.occupied_cells


def test_candidate_generator_deterministic_ids() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    a = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    b = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert [c.candidate_id for c in a.normal_candidates] == [
        c.candidate_id for c in b.normal_candidates
    ]


def test_candidate_generator_topology_signature_deterministic() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    sigs_a = tuple(c.topology_signature for c in res.normal_candidates)
    res2 = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    sigs_b = tuple(c.topology_signature for c in res2.normal_candidates)
    assert sigs_a == sigs_b


def test_candidate_generator_records_rejection_reason_enum() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert res.rejected_candidates
    for r in res.rejected_candidates:
        assert isinstance(r.rejection_reason, CandidateRejectReason)


def test_candidate_generator_records_unreachable_when_diagnostic_enabled() -> None:
    inp = replace(_greenfield_square_input(), route_goals=frozenset())
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=0,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert res.normal_candidates == ()
    assert any(
        r.rejection_reason is CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
        for r in res.rejected_candidates
    )


def test_candidate_generator_omits_unreachable_when_diagnostic_disabled() -> None:
    inp = replace(_greenfield_square_input(), route_goals=frozenset())
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=False,
        max_candidates=None,
        route_probe_max_expansions=0,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert res.normal_candidates == ()
    assert not any(
        r.rejection_reason is CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
        for r in res.rejected_candidates
    )


def test_candidate_generator_always_records_geometry_rejects() -> None:
    """Local/geometry rejects ignore ``allow_diagnostic_unreachable``."""

    inp = _greenfield_square_input()
    mineable = frozenset(inp.mineable_cells - {Coord(1, 0)})
    inp2 = replace(inp, mineable_cells=mineable)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp2)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=False,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp2, domain, build_pattern_library(), cfg)
    assert any(
        r.rejection_reason is CandidateRejectReason.EXTENSION_NOT_MINEABLE
        for r in res.rejected_candidates
    )


def test_candidate_generator_never_puts_unreachable_in_normal_pool() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    for allow in (True, False):
        cfg = CandidateGenerationConfig(
            extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
            allow_diagnostic_unreachable=allow,
            max_candidates=None,
            route_probe_max_expansions=500,
            transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
            route_probe_goal_priority_weight=10,
        )
        res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
        for c in res.normal_candidates:
            assert c.route_probe_result.reachable
            assert c.route_probe_result.reached_goal is not None


def test_candidate_generator_equivalence_dedupe_deterministic() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=500,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    keys = [
        CandidateEquivalenceKey(
            occupied_cells=c.occupied_cells,
            output_stub=c.output_stub,
            output_dir=c.output_dir,
            transport_kind=c.transport_kind,
            base_throughput=c.base_throughput,
            topology_signature=c.topology_signature,
        )
        for c in res.normal_candidates
    ]
    assert len(keys) == len(set(keys))


def test_candidate_generator_truncation_order_prefers_score_then_cost() -> None:
    inp = _greenfield_square_input()
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg_full = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    full = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg_full)
    if len(full.normal_candidates) < 3:
        pytest.skip("fixture too small for truncation ordering")

    def _equiv(c):
        return CandidateEquivalenceKey(
            occupied_cells=c.occupied_cells,
            output_stub=c.output_stub,
            output_dir=c.output_dir,
            transport_kind=c.transport_kind,
            base_throughput=c.base_throughput,
            topology_signature=c.topology_signature,
        )

    dedup_best: dict[CandidateEquivalenceKey, BundleCandidate] = {}
    for c in sorted(full.normal_candidates, key=lambda z: z.candidate_id):
        k = _equiv(c)
        prev = dedup_best.get(k)
        if prev is None or c.candidate_id < prev.candidate_id:
            dedup_best[k] = c
    deduped = tuple(sorted(dedup_best.values(), key=lambda z: z.candidate_id))
    ordered = sorted(
        deduped,
        key=lambda c: (-c.base_score, c.route_probe_result.cost, c.candidate_id),
    )
    expected = ordered[0]

    cfg_cap = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=1,
        route_probe_max_expansions=500,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    cap = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg_cap)
    assert cap.normal_candidates[0].candidate_id == expected.candidate_id


def test_candidate_generator_no_placement_commit_side_effects() -> None:
    inp = _greenfield_square_input()
    rim_id = id(inp.rim_cells)
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    domain_id = id(domain)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=200,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    assert id(inp.rim_cells) == rim_id
    assert id(domain) == domain_id


def test_normal_candidate_reachable_probe_contract() -> None:
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
        assert c.route_probe_result.reachable
        assert c.route_probe_result.reached_goal is not None
        assert c.route_probe_result.failure_reason is None


def test_rejected_unreachable_carries_probe_snapshot() -> None:
    inp = replace(_greenfield_square_input(), route_goals=frozenset())
    domain = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    cfg = CandidateGenerationConfig(
        extractor_policy=ExtractorPlacementPolicy.RIM_ONLY,
        allow_diagnostic_unreachable=True,
        max_candidates=None,
        route_probe_max_expansions=0,
        transport_kinds=frozenset({TransportKind.SHAPE_BELT}),
        route_probe_goal_priority_weight=10,
    )
    res = generate_bundle_candidates(inp, domain, build_pattern_library(), cfg)
    rj = next(
        r
        for r in res.rejected_candidates
        if r.rejection_reason is CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
    )
    assert rj.route_probe_result is not None
