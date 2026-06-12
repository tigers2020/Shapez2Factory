"""Layer 3 v2 ??DB-gene, two-phase rim placement (spec 2026-05-31-layer-03-rim-placement-v2).

Pipeline: rim anchor scan -> deterministic candidate generation + immediate route probe
(Phase B) -> deterministic beam selection (Phase C1) -> commit-time re-probe on the latest
route domain (Phase D) -> provisional ``committed_placements``. Gene templates arrive only
as a pure-core ``GeneticSampleSeedSnapshot`` (DB read stays at the Django boundary). This layer
commits nothing downstream; interior fill / final mutation remain L5/L6.
"""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedInvalid,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
    RimGreedyPolicy,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
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
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.commit_reprobe import (  # noqa: E501
    build_commit_reprobe_context,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchor_scan import (  # noqa: E501
    scan_rim_anchors,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

ALGORITHM_STUB_ID = "rim_placement_v2"


def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
) -> IntegratedRimGreedyResult:
    _ = (budget_ctx, seed_catalog, resource_kind, transport_kind)
    resolved_policy = policy or RimGreedyPolicy.default()
    if exterior_plan is None:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN.value,
            rim_anchor_count=0,
        )
    if genetic_sample_seeds is None or not genetic_sample_seeds.entries:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS.value,
            rim_anchor_count=0,
        )

    anchors = scan_rim_anchors(complete_map)
    # Phase B: per transport profile (space_belt, space_pipe) then merge pools; C1/D shared.
    try:
        candidate_set = generate_candidates(
            complete_map=complete_map,
            exterior_plan=exterior_plan,
            genetic_sample_seeds=genetic_sample_seeds,
            anchors=anchors,
        )
    except GeneticSampleSeedInvalid:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason=Layer03SkipReason.INVALID_GENETIC_SAMPLE_SEED_SNAPSHOT.value,
            rim_anchor_count=len(anchors),
        )
    commit_ctx = build_commit_reprobe_context(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    rim_anchor_coords = frozenset(anchor.coord for anchor in anchors)
    selection = select_bundles(
        candidate_set.normal_candidates,
        commit_ctx=commit_ctx,
        rim_anchor_coords=rim_anchor_coords,
        min_rim_anchor_fill_ratio=resolved_policy.min_rim_anchor_fill_ratio,
    )
    finalize = finalize_selection(
        selected=selection.selected,
        complete_map=complete_map,
        exterior_plan=exterior_plan,
    )
    return build_integrated_rim_greedy_result(
        finalize=finalize,
        selection=selection,
        rim_anchor_count=len(anchors),
        route_feasible_rim_anchor_count=candidate_set.metrics.route_feasible_rim_anchor_count,
    )


__all__ = ["ALGORITHM_STUB_ID", "run_layer_03_rim_greedy_placement"]
