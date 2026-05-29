"""Dense rim bundle candidate expansion (route-probed pool)."""

from __future__ import annotations

from collections import Counter

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RimBundleCandidateSet,
    RouteProbedBundleCandidate,
    RouteProbeStatus,
    build_rim_bundle_candidate_set,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.route_goal import build_layer03_route_goals
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
    map_resource_kind_to_transport_kind,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
    build_weighted_transport_route_domain,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.mining_footprint import (
    mining_footprint_off_field,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
    local_geometry_invalid_detail,
    project_miner_seed_at_anchor,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
    exterior_output_dir_candidates,
    sorted_outer_rim_anchors,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.route_goals import (
    derive_layer03_resource_kind,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
    MinerSeedEntry,
    load_miner_seed_catalog,
)
from django_apps.asteroid_lab.layers.shared.route_probe import weighted_route_probe
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _hold_metrics(
    *,
    rim_anchor_count: int,
    layer_skip_reason: Layer03SkipReason,
) -> Layer03ExpansionMetrics:
    return Layer03ExpansionMetrics(
        rim_anchor_count=rim_anchor_count,
        seed_projection_attempt_count=0,
        local_geometry_rejected_count=0,
        route_probe_attempt_count=0,
        route_probe_succeeded_count=0,
        route_probe_failed_count=0,
        dedupe_duplicate_count=0,
        normal_candidate_count=0,
        diagnostic_rejected_count=0,
        budget_skipped_count=0,
        layer_skip_reason=layer_skip_reason,
    )


def _geometry_diagnostic(
    *,
    anchor_coord: Coord,
    reject_reason: CandidateRejectReason,
    resource_kind: ResourceKind,
    transport_kind: TransportKind,
    output_dir: Direction = Direction.E,
) -> RouteProbedBundleCandidate:
    candidate = make_bundle_candidate_for_test(
        gene_key="diagnostic_stub",
        pattern_id="diagnostic",
        intrinsic_priority_rank=999,
        anchor_coord=anchor_coord,
        output_dir=output_dir,
        resource_kind=resource_kind,
        transport_kind=transport_kind,
    )
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=reject_reason,
    )


def _reject_histogram_key(
    entry: RouteProbedBundleCandidate,
    *,
    seed: MinerSeedEntry | None = None,
    resource_kind: ResourceKind | None = None,
    complete_map: ReconstructionCompleteMap | None = None,
) -> str:
    if entry.reject_reason is None:
        return ""
    if (
        entry.reject_reason is CandidateRejectReason.LOCAL_GEOMETRY_INVALID
        and seed is not None
        and resource_kind is not None
        and complete_map is not None
    ):
        return local_geometry_invalid_detail(
            seed=seed,
            anchor_coord=entry.candidate.anchor_coord,
            output_dir=entry.candidate.output_dir,
            resource_kind=resource_kind,
            complete_map=complete_map,
        )
    return entry.reject_reason.value


def _build_reject_reason_counts(
    diagnostics: tuple[RouteProbedBundleCandidate, ...],
    *,
    histogram_keys: tuple[str, ...] | None = None,
) -> tuple[tuple[str, int], ...]:
    tallies: Counter[str] = Counter()
    for index, entry in enumerate(diagnostics):
        if entry.reject_reason is None:
            continue
        if histogram_keys is not None and index < len(histogram_keys):
            key = histogram_keys[index]
        else:
            key = entry.reject_reason.value
        if key:
            tallies[key] += 1
    return tuple(sorted(tallies.items(), key=lambda kv: (-kv[1], kv[0])))


def _budget_skipped_diagnostic(candidate: object) -> RouteProbedBundleCandidate:
    from django_apps.asteroid_lab.layers.contracts.candidates import BundleCandidate

    assert isinstance(candidate, BundleCandidate)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SKIPPED_BUDGET,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=CandidateRejectReason.BUDGET_EXHAUSTED,
    )


def _register_succeeded(
    probed: RouteProbedBundleCandidate,
    *,
    best_by_equivalence: dict[str, RouteProbedBundleCandidate],
    dedupe_duplicate_count: int,
) -> tuple[dict[str, RouteProbedBundleCandidate], int]:
    key = probed.candidate.equivalence_key
    if key not in best_by_equivalence:
        best_by_equivalence[key] = probed
        return best_by_equivalence, dedupe_duplicate_count
    dedupe_duplicate_count += 1
    incumbent = best_by_equivalence[key]
    new_rank = probed.candidate.intrinsic_priority_rank
    old_rank = incumbent.candidate.intrinsic_priority_rank
    if new_rank < old_rank:
        best_by_equivalence[key] = probed
    elif new_rank == old_rank and probed.candidate.candidate_id < incumbent.candidate.candidate_id:
        best_by_equivalence[key] = probed
    return best_by_equivalence, dedupe_duplicate_count


def expand_rim_bundle_candidates(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: MinerSeedCatalog | None = None,
    resource_kind: ResourceKind | None = None,
) -> RimBundleCandidateSet:
    outer_rim = sorted_outer_rim_anchors(complete_map.field_cells)
    rim_anchor_count = len(outer_rim)

    if exterior_plan is None:
        return build_rim_bundle_candidate_set(
            normal_candidates=(),
            diagnostic_rejected_candidates=(),
            metrics=_hold_metrics(
                rim_anchor_count=rim_anchor_count,
                layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN,
            ),
        )

    catalog = seed_catalog or load_miner_seed_catalog()
    if not catalog.seeds:
        return build_rim_bundle_candidate_set(
            normal_candidates=(),
            diagnostic_rejected_candidates=(),
            metrics=_hold_metrics(
                rim_anchor_count=rim_anchor_count,
                layer_skip_reason=Layer03SkipReason.EMPTY_MINER_SEED_CATALOG,
            ),
        )

    resolved_resource_kind = derive_layer03_resource_kind(exterior_plan, resource_kind)
    transport_kind = map_resource_kind_to_transport_kind(resolved_resource_kind)
    route_goals = build_layer03_route_goals(exterior_plan, transport_kind=transport_kind)

    if not route_goals:
        return build_rim_bundle_candidate_set(
            normal_candidates=(),
            diagnostic_rejected_candidates=(),
            metrics=_hold_metrics(
                rim_anchor_count=rim_anchor_count,
                layer_skip_reason=Layer03SkipReason.NO_ROUTE_GOALS,
            ),
        )

    diagnostics: list[RouteProbedBundleCandidate] = []
    reject_histogram_keys: list[str] = []
    best_by_equivalence: dict[str, RouteProbedBundleCandidate] = {}
    seed_projection_attempt_count = 0
    local_geometry_rejected_count = 0
    route_probe_attempt_count = 0
    route_probe_succeeded_count = 0
    route_probe_failed_count = 0
    dedupe_duplicate_count = 0
    budget_skipped_count = 0
    exterior_direction_candidate_count = 0
    direction_seed_attempt_count = 0
    mining_footprint_prefilter_rejected_count = 0
    field_route_cell_count_total = 0
    weighted_route_cost_total = 0
    transport_blocked_by_mining_count = 0
    layer_skip_reason = Layer03SkipReason.NONE

    for anchor in outer_rim:
        if budget_ctx.remaining_budget_ms() <= 0:
            layer_skip_reason = Layer03SkipReason.BUDGET_EXHAUSTED
            break

        output_dirs = exterior_output_dir_candidates(
            anchor,
            complete_map=complete_map,
            route_goals=route_goals,
            transport_kind=transport_kind,
        )
        if not output_dirs:
            diag = _geometry_diagnostic(
                anchor_coord=anchor,
                reject_reason=CandidateRejectReason.NO_EXTERIOR_VOID_NEIGHBOR,
                resource_kind=resolved_resource_kind,
                transport_kind=transport_kind,
                output_dir=Direction.E,
            )
            diagnostics.append(diag)
            reject_histogram_keys.append(diag.reject_reason.value if diag.reject_reason else "")
            continue

        exterior_direction_candidate_count += len(output_dirs)

        for output_dir in output_dirs:
            for seed in catalog.by_intrinsic_priority_rank():
                if budget_ctx.remaining_budget_ms() <= 0:
                    layer_skip_reason = Layer03SkipReason.BUDGET_EXHAUSTED
                    break

                direction_seed_attempt_count += 1

                if mining_footprint_off_field(
                    seed=seed,
                    anchor_coord=anchor,
                    output_dir=output_dir,
                    complete_map=complete_map,
                ):
                    mining_footprint_prefilter_rejected_count += 1
                    local_geometry_rejected_count += 1
                    diag = RouteProbedBundleCandidate(
                        candidate=make_bundle_candidate_for_test(
                            anchor_coord=anchor,
                            output_dir=output_dir,
                            resource_kind=resolved_resource_kind,
                            transport_kind=transport_kind,
                        ),
                        route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
                        route_probe_result=None,
                        route_goal_id=None,
                        reject_reason=CandidateRejectReason.MINING_CELL_OFF_FIELD,
                    )
                    diagnostics.append(diag)
                    reject_histogram_keys.append(
                        CandidateRejectReason.MINING_CELL_OFF_FIELD.value,
                    )
                    continue

                seed_projection_attempt_count += 1
                projection = project_miner_seed_at_anchor(
                    seed=seed,
                    anchor_coord=anchor,
                    output_dir=output_dir,
                    resource_kind=resolved_resource_kind,
                    transport_kind=transport_kind,
                    complete_map=complete_map,
                )
                if projection.candidate is None:
                    local_geometry_rejected_count += 1
                    if (
                        projection.reject_reason
                        is CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT
                    ):
                        transport_blocked_by_mining_count += 1
                    diag = RouteProbedBundleCandidate(
                        candidate=make_bundle_candidate_for_test(
                            anchor_coord=anchor,
                            output_dir=output_dir,
                            resource_kind=resolved_resource_kind,
                            transport_kind=transport_kind,
                        ),
                        route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
                        route_probe_result=None,
                        route_goal_id=None,
                        reject_reason=projection.reject_reason,
                    )
                    diagnostics.append(diag)
                    reject_histogram_keys.append(
                        _reject_histogram_key(
                            diag,
                            seed=seed,
                            resource_kind=resolved_resource_kind,
                            complete_map=complete_map,
                        ),
                    )
                    continue

                candidate = projection.candidate
                domain = build_weighted_transport_route_domain(
                    complete_map=complete_map,
                    anchor_abs=anchor,
                    transport_entry_coord=candidate.route_probe_start_coord,
                    transport_stub_cells=candidate.transport_stub_cells,
                    route_goals=route_goals,
                    mining_occupied_cells=candidate.mining_occupied_cells,
                )
                if domain.step_cost(candidate.route_probe_start_coord) is None:
                    local_geometry_rejected_count += 1
                    diag = RouteProbedBundleCandidate(
                        candidate=candidate,
                        route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
                        route_probe_result=None,
                        route_goal_id=None,
                        reject_reason=CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
                    )
                    diagnostics.append(diag)
                    reject_histogram_keys.append(
                        CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE.value,
                    )
                    continue

                if budget_ctx.remaining_budget_ms() <= 0:
                    diagnostics.append(_budget_skipped_diagnostic(candidate))
                    reject_histogram_keys.append(CandidateRejectReason.BUDGET_EXHAUSTED.value)
                    budget_skipped_count += 1
                    layer_skip_reason = Layer03SkipReason.BUDGET_EXHAUSTED
                    break

                route_probe_attempt_count += 1
                probed = weighted_route_probe(
                    candidate=candidate,
                    route_goals=route_goals,
                    domain=domain,
                    field_cells=complete_map.field_cells,
                )

                if probed.route_probe_status == RouteProbeStatus.SUCCEEDED:
                    route_probe_succeeded_count += 1
                    if probed.route_probe_result is not None:
                        field_route_cell_count_total += (
                            probed.route_probe_result.field_route_cell_count
                        )
                        weighted_route_cost_total += probed.route_probe_result.route_cost
                    best_by_equivalence, dedupe_duplicate_count = _register_succeeded(
                        probed,
                        best_by_equivalence=best_by_equivalence,
                        dedupe_duplicate_count=dedupe_duplicate_count,
                    )
                elif probed.route_probe_status == RouteProbeStatus.FAILED:
                    route_probe_failed_count += 1
                    diagnostics.append(probed)
                    reject_histogram_keys.append(
                        probed.reject_reason.value if probed.reject_reason else "",
                    )
                else:
                    diagnostics.append(probed)
                    reject_histogram_keys.append(
                        probed.reject_reason.value if probed.reject_reason else "",
                    )

            if layer_skip_reason is Layer03SkipReason.BUDGET_EXHAUSTED:
                break

        if layer_skip_reason is Layer03SkipReason.BUDGET_EXHAUSTED:
            break

    normal_sorted = tuple(
        sorted(
            best_by_equivalence.values(),
            key=lambda p: (
                p.candidate.anchor_coord[1],
                p.candidate.anchor_coord[0],
                p.candidate.intrinsic_priority_rank,
                p.candidate.candidate_id,
            ),
        )
    )

    diagnostic_tuple = tuple(diagnostics)
    metrics = Layer03ExpansionMetrics(
        rim_anchor_count=rim_anchor_count,
        seed_projection_attempt_count=seed_projection_attempt_count,
        local_geometry_rejected_count=local_geometry_rejected_count,
        route_probe_attempt_count=route_probe_attempt_count,
        route_probe_succeeded_count=route_probe_succeeded_count,
        route_probe_failed_count=route_probe_failed_count,
        dedupe_duplicate_count=dedupe_duplicate_count,
        normal_candidate_count=len(normal_sorted),
        diagnostic_rejected_count=len(diagnostic_tuple),
        budget_skipped_count=budget_skipped_count,
        layer_skip_reason=layer_skip_reason,
        reject_reason_counts=_build_reject_reason_counts(
            diagnostic_tuple,
            histogram_keys=tuple(reject_histogram_keys),
        ),
        exterior_direction_candidate_count=exterior_direction_candidate_count,
        direction_seed_attempt_count=direction_seed_attempt_count,
        mining_footprint_prefilter_rejected_count=mining_footprint_prefilter_rejected_count,
        field_route_cell_count_total=field_route_cell_count_total,
        weighted_route_cost_total=weighted_route_cost_total,
        transport_blocked_by_mining_count=transport_blocked_by_mining_count,
    )
    return build_rim_bundle_candidate_set(
        normal_candidates=normal_sorted,
        diagnostic_rejected_candidates=diagnostic_tuple,
        metrics=metrics,
    )


__all__ = ["expand_rim_bundle_candidates"]
