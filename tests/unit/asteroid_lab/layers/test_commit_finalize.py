"""Layer 03 Phase D ??commit-time re-probe + integrated result assembly + v2 run wiring.

Covers: surviving bundles become provisional committed_placements, the re-probe blocks a
later bundle that collides with already-committed equipment (candidate reachability is never
the final commit proof), and the canonical IntegratedRimGreedyResult is well-formed.
"""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyRejectReason,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.beam_selector import (  # noqa: E501
    select_bundles,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (  # noqa: E501
    generate_candidates,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_finalize import (  # noqa: E501
    build_integrated_rim_greedy_result,
    finalize_selection,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def _m0e_entry() -> GeneticSampleSeedEntry:
    return GeneticSampleSeedEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e_base",
    )


def _m3e_entry() -> GeneticSampleSeedEntry:
    return GeneticSampleSeedEntry(
        gene_id="m3e",
        resource_kind="shape",
        canonical_output_dir="E",
        occupied_offsets=((0, 0), (-1, 0), (-2, 0), (-3, 0)),
        extractor_offset=(0, 0),
        extension_offsets=((-1, 0), (-2, 0), (-3, 0)),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=16,
        topology_signature_base="m3e_base",
    )


def _catalog() -> GeneticSampleSeedSnapshot:
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(_m3e_entry(), _m0e_entry()),
    )


def _golden_normal() -> tuple:
    result = generate_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        genetic_sample_seeds=_catalog(),
    )
    return result.normal_candidates


def test_finalize_commits_the_selected_bundle_to_the_goal() -> None:
    selection = select_bundles(_golden_normal())
    finalize = finalize_selection(
        selected=selection.selected,
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
    )
    assert len(finalize.committed_placements) == 1
    placement = finalize.committed_placements[0]
    assert placement.seed_id == "m3e"
    assert placement.anchor == (6, 4)
    assert placement.route_probe_path[-1] == (8, 4)
    # the committed extractor + extensions occupy the field; the reserved route holds the goal.
    assert {(6, 4), (5, 4), (4, 4), (3, 4)} <= finalize.occupied_equipment_cells
    assert (8, 4) in finalize.reserved_route_cells


def test_finalize_reprobe_drops_a_bundle_colliding_with_committed_equipment() -> None:
    # Feed the finalizer an overlapping pair (both occupy extractor (6,4)). The first commits;
    # the re-probe MUST reject the second for equipment collision rather than double-place.
    normal = _golden_normal()
    by_gene = {p.candidate.gene_key: p for p in normal}
    selection = select_bundles((by_gene["m3e"], by_gene["m0e"]))
    # selector already drops m0e for overlap, so feed finalize the raw overlapping pair:
    finalize = finalize_selection(
        selected=(by_gene["m3e"], by_gene["m0e"]),
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
    )
    assert len(finalize.committed_placements) == 1
    assert finalize.committed_placements[0].seed_id == "m3e"
    assert len(finalize.rejected_attempts) == 1
    assert finalize.rejected_attempts[0].reason == RimGreedyRejectReason.EQUIPMENT_COLLISION
    assert selection.rejected_overlap_count == 1


def test_build_integrated_result_is_well_formed() -> None:
    selection = select_bundles(_golden_normal())
    finalize = finalize_selection(
        selected=selection.selected,
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
    )
    result = build_integrated_rim_greedy_result(
        finalize=finalize, selection=selection, rim_anchor_count=12
    )
    assert result.metrics.committed_placement_count == 1
    assert result.metrics.layer_skip_reason is None
    assert result.pass2_report.hard_fail is False
    assert result.winning_variant_id
    # overlay by_cell keys must equal occupied_cells (DTO invariant) and cover the equipment.
    assert frozenset(result.provisional_overlay.by_cell.keys()) == (
        result.provisional_overlay.occupied_cells
    )
    assert result.append_result.placement_count == 1


def test_commit_aware_beam_finalize_has_no_rejects_on_golden() -> None:
    from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_reprobe import (  # noqa: E501
        build_commit_reprobe_context,
    )

    complete_map = golden_5x5_complete_map()
    exterior_plan = minimal_l2_plan_for_golden()
    commit_ctx = build_commit_reprobe_context(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert commit_ctx is not None
    selection = select_bundles(_golden_normal(), commit_ctx=commit_ctx)
    finalize = finalize_selection(
        selected=selection.selected,
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    assert len(finalize.committed_placements) >= 1
    assert finalize.rejected_attempts == ()


def test_run_layer_03_v2_end_to_end_commits_one_placement() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=_catalog(),
    )
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.committed_placement_count == 1
    assert result.committed_placements[0].seed_id == "m3e"
    assert result.metrics.rim_anchor_count > 0


def test_run_layer_03_v2_MISSING_GENETIC_SAMPLE_SEEDS_skips() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=None,
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS.value
    assert result.committed_placements == ()
