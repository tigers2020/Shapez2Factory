"""Candidate generator tests (Solver Runtime PR3)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch, wraps

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    build_normal_gene_candidate,
    make_topology_signature,
)
from django_apps.asteroid_lab.optimization.candidate_equivalence import dedupe_gene_candidates
from django_apps.asteroid_lab.optimization.candidate_generator import (
    _truncate_with_anchor_floor,
    default_generation_config,
    generate_gene_candidates,
)
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    Direction,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.gene_projection import project_gene_placement
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    RouteGoal,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _minimal_gene():
    return load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")[0]


def _reachable_void_input(*, bb: BBox | None = None):
    bb = bb or BBox(0, 6, 0, 0)
    mineable = frozenset({(0, 0)})
    void = frozenset((sx, 0) for sx in range(bb.min_sx, bb.max_sx + 1))
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    return replace(
        greenfield_optimization_input(bbox=bb),
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=mineable,
        external_void_cells=void,
        route_goals=frozenset({goal}),
    )


def _two_rim_reachable_input():
    bb = BBox(0, 6, 0, 0)
    mineable = frozenset({(0, 0), (2, 0)})
    void = frozenset((sx, 0) for sx in range(bb.min_sx, bb.max_sx + 1))
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    return replace(
        greenfield_optimization_input(bbox=bb),
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=mineable,
        external_void_cells=void,
        route_goals=frozenset({goal}),
    )


def _default_config(**kwargs):
    return replace(default_generation_config(), **kwargs)


def _probe_result_for(gene, inp):
    projected = project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
    domain = build_route_domain_for_projected_gene_probe(inp, projected)
    return run_route_probe(
        RouteProbeInput(
            start=projected.route_probe_start,
            goals=inp.route_goals,
            route_domain=domain,
            topology_graph=inp.topology_graph,
            max_expansions=500,
            transport_kind=TransportKind.SHAPE_BELT,
        )
    )


def test_candidate_generator_reachable_only_enters_normal_pool() -> None:
    inp = _reachable_void_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())

    assert len(result.normal_candidates) >= 1
    assert all(c.route_probe_result.reachable for c in result.normal_candidates)
    assert all(c.route_probe_result.reached_goal is not None for c in result.normal_candidates)
    assert not any(
        r.rejection_reason == CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
        for r in result.rejected_candidates
        if r.route_probe_result and r.route_probe_result.reachable
    )


def test_candidate_generator_rejects_unreachable() -> None:
    inp = _reachable_void_input()
    inp = replace(inp, route_goals=frozenset())
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())

    assert result.normal_candidates == ()
    assert any(
        r.rejection_reason == CandidateRejectReason.ROUTE_PROBE_UNREACHABLE
        for r in result.rejected_candidates
    )


def test_dedupe_gene_candidates_keeps_lowest_candidate_id() -> None:
    inp = _reachable_void_input()
    gene = _minimal_gene()
    projected = project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
    probe_result = _probe_result_for(gene, inp)
    base = build_normal_gene_candidate(
        gene=gene,
        projected=projected,
        rotation=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        route_probe_result=probe_result,
    )
    dup_low = replace(base, candidate_id="a:0,0:e:shape_belt")
    dup_high = replace(base, candidate_id="z:0,0:e:shape_belt")

    deduped = dedupe_gene_candidates((dup_high, dup_low))
    assert deduped == (dup_low,)


def test_generation_diagnostics_counts_reachable_before_dedupe() -> None:
    inp = _two_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())

    diag = result.generation_diagnostics
    assert diag.rim_cell_count == len(inp.rim_cells) == 2
    assert diag.reachable_anchors_after_prefilter_count >= 1
    assert diag.reachable_anchors_after_prefilter_count <= diag.rim_cell_count
    assert len({c.extractor for c in result.normal_candidates}) <= (
        diag.reachable_anchors_after_prefilter_count
    )


def _five_rim_reachable_input():
    bb = BBox(0, 10, 0, 0)
    mineable = frozenset((sx, 0) for sx in range(0, 10, 2))
    void = frozenset((sx, 0) for sx in range(bb.min_sx, bb.max_sx + 1))
    goal = RouteGoal(
        coord=(10, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    return replace(
        greenfield_optimization_input(bbox=bb),
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=mineable,
        external_void_cells=void,
        route_goals=frozenset({goal}),
    )


def _candidates_for_rim_anchors(inp, gene, anchors: tuple[tuple[int, int], ...]):
    out = []
    for anchor in anchors:
        projected = project_gene_placement(anchor=anchor, rotation=Direction.E, gene=gene)
        domain = build_route_domain_for_projected_gene_probe(inp, projected)
        probe = run_route_probe(
            RouteProbeInput(
                start=projected.route_probe_start,
                goals=inp.route_goals,
                route_domain=domain,
                topology_graph=inp.topology_graph,
                max_expansions=256,
                transport_kind=TransportKind.SHAPE_BELT,
            )
        )
        out.append(
            build_normal_gene_candidate(
                gene=gene,
                projected=projected,
                rotation=Direction.E,
                transport_kind=TransportKind.SHAPE_BELT,
                route_probe_result=probe,
            )
        )
    return tuple(out)


def test_anchor_floor_preserves_distinct_extractors_before_fill() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    anchors = tuple(sorted(inp.rim_cells))
    raw = _candidates_for_rim_anchors(inp, gene, anchors)
    deduped = dedupe_gene_candidates(raw)
    truncated = _truncate_with_anchor_floor(deduped, max_candidates=len(anchors))

    assert len({c.extractor for c in truncated}) == len(anchors)


def test_anchor_floor_caps_when_anchors_exceed_max() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    anchors = tuple(sorted(inp.rim_cells))
    deduped = dedupe_gene_candidates(_candidates_for_rim_anchors(inp, gene, anchors))
    max_candidates = 3
    truncated = _truncate_with_anchor_floor(deduped, max_candidates=max_candidates)

    assert len(truncated) == max_candidates
    assert len({c.extractor for c in truncated}) == max_candidates


def test_probe_budget_preserves_distinct_extractors() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(
        inp,
        (gene,),
        _default_config(max_candidates=3, probe_budget_factor=1),
    )
    diag = result.generation_diagnostics
    assert diag.unique_anchors_after_probe_budget_count == 3
    assert diag.probe_budget_floor_reserved_count >= 3


def test_probe_budget_floor_reserved_and_fill_counts() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(
        inp,
        (gene,),
        _default_config(max_candidates=10, probe_budget_factor=1),
    )
    diag = result.generation_diagnostics
    assert diag.probe_budget_floor_reserved_count >= 5
    assert diag.probe_budget_floor_reserved_count + diag.probe_budget_fill_count <= 10


def test_funnel_identity_probe_plus_dedupe() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())
    diag = result.generation_diagnostics
    assert (
        diag.anchors_dropped_by_probe_budget_count + diag.unique_anchors_after_probe_budget_count
        == diag.reachable_anchors_after_prefilter_count
    )


def test_generation_truncation_metrics_identity() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(
        inp,
        (gene,),
        _default_config(max_candidates=3),
    )
    diag = result.generation_diagnostics
    assert (
        diag.anchor_preserved_by_truncation_count + diag.anchor_dropped_by_truncation_count
        == diag.unique_anchors_after_dedupe_count
    )
    assert diag.unique_anchors_after_dedupe_count >= 5


def test_generation_truncated_by_max_candidates_count() -> None:
    inp = _five_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(
        inp,
        (gene,),
        _default_config(max_candidates=2),
    )
    diag = result.generation_diagnostics
    assert result.deduped_candidate_count >= 5
    assert len(result.normal_candidates) == 2
    assert len({c.extractor for c in result.normal_candidates}) == 2
    assert diag.truncated_by_max_candidates_count == result.deduped_candidate_count - 2
    assert diag.truncated_by_max_candidates_count > 0
    assert diag.anchor_dropped_by_truncation_count == (diag.unique_anchors_after_dedupe_count - 2)


def test_candidate_generator_dedupes_before_max_candidates() -> None:
    inp = _two_rim_reachable_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(
        inp,
        (gene,),
        _default_config(max_candidates=1),
    )
    assert len(result.normal_candidates) == 1


def test_candidate_generator_does_not_commit_placements() -> None:
    inp = _reachable_void_input()
    before = inp
    gene = _minimal_gene()
    generate_gene_candidates(inp, (gene,), _default_config())
    assert inp == before


def test_candidate_generator_uses_server_coords_only() -> None:
    inp = _reachable_void_input()
    gene = _minimal_gene()
    with patch(
        "django_apps.asteroid_lab.snapshots.server_coords.server_xy_for_raw_xy",
    ) as mock_raw:
        generate_gene_candidates(inp, (gene,), _default_config())
        mock_raw.assert_not_called()


def test_candidate_id_is_deterministic() -> None:
    inp = _reachable_void_input()
    gene = _minimal_gene()
    config = _default_config()
    first = generate_gene_candidates(inp, (gene,), config).normal_candidates
    second = generate_gene_candidates(inp, (gene,), config).normal_candidates
    ids_a = {c.candidate_id for c in first}
    ids_b = {c.candidate_id for c in second}
    assert ids_a == ids_b
    assert ids_a


def test_candidate_generator_records_rejection_reason_enum() -> None:
    inp = _reachable_void_input()
    inp = replace(inp, route_goals=frozenset())
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())

    assert result.rejected_candidates
    reasons = {r.rejection_reason for r in result.rejected_candidates}
    assert CandidateRejectReason.ROUTE_PROBE_UNREACHABLE in reasons
    assert all(isinstance(reason, CandidateRejectReason) for reason in reasons)


def test_topology_signature_deterministic() -> None:
    gene = _minimal_gene()
    projected = project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
    sig_a = make_topology_signature(
        gene=gene,
        projected=projected,
        rotation=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    sig_b = make_topology_signature(
        gene=gene,
        projected=projected,
        rotation=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert sig_a == sig_b


def test_build_normal_gene_candidate_rejects_unreachable_probe() -> None:
    import pytest

    inp = _reachable_void_input()
    gene = _minimal_gene()
    projected = project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
    domain = build_route_domain_for_projected_gene_probe(inp, projected)
    bad = run_route_probe(
        RouteProbeInput(
            start=projected.route_probe_start,
            goals=frozenset(),
            route_domain=domain,
            topology_graph=inp.topology_graph,
            max_expansions=10,
            transport_kind=TransportKind.SHAPE_BELT,
        )
    )
    with pytest.raises(ValueError, match="reachable"):
        build_normal_gene_candidate(
            gene=gene,
            projected=projected,
            rotation=Direction.E,
            transport_kind=TransportKind.SHAPE_BELT,
            route_probe_result=bad,
        )


def test_dedupe_skips_duplicate_route_probe() -> None:
    inp = _two_rim_reachable_input()
    gene = _minimal_gene()
    config = _default_config(route_probe_max_expansions=256)
    call_count = 0
    original = run_route_probe

    @wraps(original)
    def counting_probe(probe):
        nonlocal call_count
        call_count += 1
        return original(probe)

    with patch(
        "django_apps.asteroid_lab.optimization.candidate_generator.run_route_probe",
        side_effect=counting_probe,
    ):
        result = generate_gene_candidates(inp, (gene,), config)

    naive_upper = len(inp.rim_cells) * 4 * len(config.transport_kinds)
    assert call_count <= naive_upper
    assert result.timing is not None
    assert result.timing.route_probe_count == call_count
    assert call_count <= naive_upper


def test_candidate_generator_exposes_timing() -> None:
    inp = _reachable_void_input()
    gene = _minimal_gene()
    result = generate_gene_candidates(inp, (gene,), _default_config())
    assert result.timing is not None
    assert result.timing.route_probe_count >= 0
    assert result.timing.candidate_generation_ms >= 0.0


def test_probe_budget_caps_route_probe_count() -> None:
    inp = _two_rim_reachable_input()
    gene = _minimal_gene()
    config = _default_config(max_candidates=1, probe_budget_factor=2)
    result = generate_gene_candidates(inp, (gene,), config)
    assert result.timing is not None
    assert result.timing.route_probe_count <= 2


def test_base_reverse_bfs_runs_once_per_transport_kind() -> None:
    from django_apps.asteroid_lab.optimization.route_distance_cache import (
        _build_reverse_distance_map,
    )

    inp = _two_rim_reachable_input()
    gene = _minimal_gene()
    config = _default_config()
    bfs_calls = 0
    original = _build_reverse_distance_map

    @wraps(original)
    def counting_bfs(*args, **kwargs):
        nonlocal bfs_calls
        bfs_calls += 1
        return original(*args, **kwargs)

    with patch(
        "django_apps.asteroid_lab.optimization.candidate_generator._build_reverse_distance_map",
        side_effect=counting_bfs,
    ):
        generate_gene_candidates(inp, (gene,), config)

    assert bfs_calls == len(config.transport_kinds)
