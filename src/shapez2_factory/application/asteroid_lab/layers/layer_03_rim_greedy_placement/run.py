"""Layer 3 — integrated rim greedy placement."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
    RimGreedyMetrics,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPolicy,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    build_empty_layer03_append_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.append import (
    append_committed_rim_placements,
    provisional_overlay_from_append,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_pass1 import (  # noqa: E501
    run_pass1_for_variant,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_pass2 import (  # noqa: E501
    score_variant,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (  # noqa: E501
    DEFAULT_GREEDY_SEEDS,
    GreedyMinerSeed,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchors import (  # noqa: E501
    build_ordered_outer_rim_anchors,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.traversal_variants import (  # noqa: E501
    VARIANT_IDS,
    build_variant_anchor_order,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _resolve_seeds(seed_catalog: object | None) -> tuple[GreedyMinerSeed, ...]:
    if seed_catalog is None:
        return DEFAULT_GREEDY_SEEDS
    if isinstance(seed_catalog, tuple):
        return tuple(s for s in seed_catalog if isinstance(s, GreedyMinerSeed))
    return ()


def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
) -> IntegratedRimGreedyResult:
    _ = (budget_ctx, resource_kind)
    effective_policy = policy or RimGreedyPolicy.default()
    anchors = build_ordered_outer_rim_anchors(complete_map)
    rim_anchor_count = len(anchors)

    if exterior_plan is None:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason="missing_exterior_connection_plan",
            rim_anchor_count=rim_anchor_count,
        )

    seeds = _resolve_seeds(seed_catalog)
    if not seeds:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason="empty_miner_seed_catalog",
            rim_anchor_count=rim_anchor_count,
        )

    effective_transport = transport_kind or TransportKind.SHAPE_BELT
    route_goals = build_layer03_route_goals(
        exterior_plan,
        transport_kind=effective_transport,
    )
    if not route_goals:
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason="no_route_goals",
            rim_anchor_count=rim_anchor_count,
        )

    seeds_by_id = {s.seed_id: s for s in seeds}
    all_events: list[RimGreedyObservationEvent] = []
    best_state = None
    best_report = None
    best_key: tuple[float, str] = (float("-inf"), "")

    for variant_id in VARIANT_IDS:
        variant_anchors = build_variant_anchor_order(anchors, variant_id)
        state = run_pass1_for_variant(
            variant_id=variant_id,
            variant_anchors=variant_anchors,
            seeds=seeds,
            complete_map=complete_map,
            route_goals=route_goals,
            policy=effective_policy,
            transport_kind=effective_transport,
        )
        report = score_variant(
            state,
            complete_map=complete_map,
            route_goals=route_goals,
            policy=effective_policy,
            transport_kind=effective_transport,
            seeds_by_id=seeds_by_id,
        )
        all_events.extend(state.observability_events)
        score_value = report.score if report.score is not None else float("-inf")
        key = (score_value, variant_id)
        if key > best_key:
            best_key = key
            best_state = state
            best_report = report

    assert best_state is not None and best_report is not None
    committed = tuple(best_state.committed_placements)
    append_result = (
        append_committed_rim_placements(committed_placements=committed)
        if committed
        else build_empty_layer03_append_result()
    )
    overlay = provisional_overlay_from_append(
        append_result,
        transport_kind=effective_transport,
    )
    all_events.append(
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_COMPLETE,
            variant_id=best_state.variant_id,
            payload={
                "winning_variant_id": best_state.variant_id,
                "pass2_score": best_report.score,
            },
        )
    )
    metrics = RimGreedyMetrics(
        rim_anchor_count=rim_anchor_count,
        committed_placement_count=len(best_state.committed_placements),
        rejected_attempt_count=len(best_state.rejected_attempts),
        reserved_route_cell_count=len(best_state.reserved_route_cells),
        winning_variant_id=best_state.variant_id,
        pass2_score=best_report.score,
    )
    return IntegratedRimGreedyResult(
        committed_placements=tuple(best_state.committed_placements),
        rejected_attempts=tuple(best_state.rejected_attempts),
        occupied_equipment_cells=frozenset(best_state.occupied_equipment_cells),
        reserved_route_cells=frozenset(best_state.reserved_route_cells),
        append_result=append_result,
        provisional_overlay=overlay,
        pass2_report=best_report,
        winning_variant_id=best_state.variant_id,
        metrics=metrics,
        observability_events=tuple(all_events),
    )


__all__ = ["run_layer_03_rim_greedy_placement"]
