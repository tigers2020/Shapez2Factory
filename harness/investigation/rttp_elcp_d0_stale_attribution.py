"""P1-ELCP-RF-D0: overlap-pack stale_candidate_reachable attribution (not solver input).

``new_blocking_cells_since_last_commit_count`` is attribution evidence, not by itself
proof that the immediately preceding commit caused the stale failure.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any
from unittest.mock import patch

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitResult,
    incremental_commit,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from harness.investigation.rttp_elcp_c0_dual_mode import (
    build_gate_a_rf1_inputs,
    resolve_git_sha,
)
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpAttemptLedgerRow,
    ElcpProbeFailureClass,
    MirrorDomainSnapshot,
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
)

_DOMAIN_CONGESTION_ROUTE_CELL_RATIO = 0.15
_D0_VERDICT_DOMINANCE_THRESHOLD = 0.50
_NEW_BLOCKING_SAMPLE_MAX = 10

RESERVATION_CONFLICT_REASONS: frozenset[str] = frozenset(
    {
        "overlap",
        "route_cell_conflict",
        "occupied_cell_conflict",
        "output_stub_not_reserved",
        "fixed_output_transport_conflict",
        "fixed_output_transport_inside_mineable",
        "hard_protected_conflict",
        "inlet_on_shared_transport",
    }
)


class ElcpStaleAttributionClass(StrEnum):
    POST_PROBE_RESERVATION_BLOCK = "post_probe_reservation_block"
    POST_PROBE_POLICY_BLOCK = "post_probe_policy_block"
    PROBE_START_DRIFT = "probe_start_drift"
    GOAL_SET_SHRINK = "goal_set_shrink"
    DOMAIN_CONGESTION_AT_COMMIT = "domain_congestion_at_commit"
    SELECTION_SURVIVABILITY_GAP = "selection_survivability_gap"
    UNATTRIBUTED_STALE = "unattributed_stale"


class ElcpD0Verdict(StrEnum):
    RESERVATION_DRIFT_DOMINANT = "reservation_drift_dominant"
    GOAL_OR_DOMAIN_DRIFT_DOMINANT = "goal_or_domain_drift_dominant"
    SELECTION_COMMIT_SURVIVABILITY_GAP = "selection_commit_survivability_gap"
    INCONCLUSIVE_NEEDS_TELEMETRY = "inconclusive_needs_telemetry"


@dataclass(frozen=True, slots=True)
class ElcpStaleAttributionRow:
    commit_index: int
    candidate_id: str
    probe_failure_class: str
    stale_attribution_class: ElcpStaleAttributionClass
    commit_conflict_reason: str | None
    candidate_route_probe_reachable: bool
    commit_probe_reachable: bool
    probe_start: Coord | None
    candidate_route_probe_start: Coord | None
    committed_route_cell_count: int
    new_blocking_cells_since_last_commit_count: int
    new_blocking_cells_sample: tuple[Coord, ...]
    probe_expanded_nodes: int | None
    probe_max_expansions: int
    domain_version: int
    deferred_retry_eligible: bool
    assigned_lane_id: str | None
    git_sha: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_index": self.commit_index,
            "candidate_id": self.candidate_id,
            "probe_failure_class": self.probe_failure_class,
            "stale_attribution_class": self.stale_attribution_class.value,
            "commit_conflict_reason": self.commit_conflict_reason,
            "candidate_route_probe_reachable": self.candidate_route_probe_reachable,
            "commit_probe_reachable": self.commit_probe_reachable,
            "probe_start": list(self.probe_start) if self.probe_start else None,
            "candidate_route_probe_start": (
                list(self.candidate_route_probe_start) if self.candidate_route_probe_start else None
            ),
            "committed_route_cell_count": self.committed_route_cell_count,
            "new_blocking_cells_since_last_commit_count": (
                self.new_blocking_cells_since_last_commit_count
            ),
            "new_blocking_cells_sample": [list(c) for c in self.new_blocking_cells_sample],
            "probe_expanded_nodes": self.probe_expanded_nodes,
            "probe_max_expansions": self.probe_max_expansions,
            "domain_version": self.domain_version,
            "deferred_retry_eligible": self.deferred_retry_eligible,
            "assigned_lane_id": self.assigned_lane_id,
            "git_sha": self.git_sha,
        }


@dataclass(frozen=True, slots=True)
class ElcpD0ForensicsResult:
    git_sha: str
    rows: tuple[ElcpStaleAttributionRow, ...]
    histogram: dict[str, int]
    verdict: ElcpD0Verdict
    attribution_coverage: float
    unattributed_ratio: float
    c0_carry_forward: dict[str, Any]


def diff_blocking_cells(
    *,
    before: MirrorDomainSnapshot | None,
    at_attempt: MirrorDomainSnapshot,
) -> tuple[int, tuple[Coord, ...]]:
    at_union = frozenset(at_attempt.committed_route_cells | at_attempt.committed_occupied)
    if before is None:
        before_union: frozenset[Coord] = frozenset()
    else:
        before_union = frozenset(before.committed_route_cells | before.committed_occupied)
    diff = sorted(at_union - before_union)
    sample = tuple(diff[:_NEW_BLOCKING_SAMPLE_MAX])
    return len(diff), sample


def _snapshot_before_commit_index(
    snapshots: Sequence[MirrorDomainSnapshot],
    commit_index: int,
) -> MirrorDomainSnapshot | None:
    prior = [s for s in snapshots if s.commit_index < commit_index]
    if not prior:
        return None
    return max(prior, key=lambda s: s.commit_index)


def _at_attempt_by_index(
    snapshots: Sequence[MirrorDomainSnapshot],
) -> dict[int, MirrorDomainSnapshot]:
    return {s.commit_index: s for s in snapshots}


def classify_stale_attribution(
    *,
    probe_failure_class: ElcpProbeFailureClass,
    commit_probe_reachable: bool,
    commit_conflict_reason: str | None,
    probe_start: Coord | None,
    candidate_route_probe_start: Coord | None,
    goals_nonempty_at_commit: bool,
    global_goal_count: int,
    committed_route_cell_count: int,
    traversable_cell_count: int,
    new_blocking_cells_since_last_commit_count: int,
) -> ElcpStaleAttributionClass:
    if probe_failure_class is not ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE:
        return ElcpStaleAttributionClass.UNATTRIBUTED_STALE

    if commit_probe_reachable and commit_conflict_reason in RESERVATION_CONFLICT_REASONS:
        return ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK

    if commit_probe_reachable and commit_conflict_reason is not None:
        return ElcpStaleAttributionClass.POST_PROBE_POLICY_BLOCK

    if (
        probe_start is not None
        and candidate_route_probe_start is not None
        and probe_start != candidate_route_probe_start
    ):
        return ElcpStaleAttributionClass.PROBE_START_DRIFT

    if global_goal_count > 0 and not goals_nonempty_at_commit:
        return ElcpStaleAttributionClass.GOAL_SET_SHRINK

    if (
        traversable_cell_count > 0
        and committed_route_cell_count / traversable_cell_count
        >= _DOMAIN_CONGESTION_ROUTE_CELL_RATIO
    ):
        return ElcpStaleAttributionClass.DOMAIN_CONGESTION_AT_COMMIT

    return ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP


def compute_d0_verdict(
    *,
    attribution_classes: Sequence[ElcpStaleAttributionClass],
    new_blocking_cells_counts: Sequence[int],
    reservation_conflict_flags: Sequence[bool],
) -> ElcpD0Verdict:
    n = len(attribution_classes)
    if n == 0:
        return ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY

    unattributed = sum(
        1 for c in attribution_classes if c is ElcpStaleAttributionClass.UNATTRIBUTED_STALE
    )
    if unattributed / n > 0.10:
        return ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY

    threshold = _D0_VERDICT_DOMINANCE_THRESHOLD

    reservation_count = sum(
        1
        for cls, blocking, res_flag in zip(
            attribution_classes,
            new_blocking_cells_counts,
            reservation_conflict_flags,
            strict=True,
        )
        if cls is ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK
        or (blocking > 0 and res_flag)
    )
    goal_domain_count = sum(
        1
        for cls in attribution_classes
        if cls
        in (
            ElcpStaleAttributionClass.GOAL_SET_SHRINK,
            ElcpStaleAttributionClass.PROBE_START_DRIFT,
            ElcpStaleAttributionClass.DOMAIN_CONGESTION_AT_COMMIT,
        )
    )
    survivability_count = sum(
        1
        for cls in attribution_classes
        if cls is ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP
    )

    scores: list[tuple[ElcpD0Verdict, int]] = [
        (ElcpD0Verdict.RESERVATION_DRIFT_DOMINANT, reservation_count),
        (ElcpD0Verdict.GOAL_OR_DOMAIN_DRIFT_DOMINANT, goal_domain_count),
        (ElcpD0Verdict.SELECTION_COMMIT_SURVIVABILITY_GAP, survivability_count),
    ]
    scores.sort(key=lambda item: item[1], reverse=True)
    top_verdict, top_count = scores[0]
    second_count = scores[1][1] if len(scores) > 1 else 0

    if top_count / n < threshold:
        return ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY
    if top_count == second_count:
        return ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY
    return top_verdict


def build_stale_attribution_rows(
    *,
    ledger: Sequence[ElcpAttemptLedgerRow],
    snapshots_after_success: Sequence[MirrorDomainSnapshot],
    snapshots_at_attempt: Sequence[MirrorDomainSnapshot],
    candidates_by_id: Mapping[str, BundleCandidate],
    global_goal_count: int,
    traversable_by_commit_index: Mapping[int, int],
    git_sha: str,
) -> tuple[ElcpStaleAttributionRow, ...]:
    at_attempt = _at_attempt_by_index(snapshots_at_attempt)
    rows: list[ElcpStaleAttributionRow] = []

    for entry in ledger:
        if entry.probe_failure_class is not ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE:
            continue
        candidate = candidates_by_id[entry.candidate_id]
        attempt_snap = at_attempt[entry.commit_index]
        before = _snapshot_before_commit_index(
            snapshots_after_success,
            entry.commit_index,
        )
        blocking_count, blocking_sample = diff_blocking_cells(
            before=before,
            at_attempt=attempt_snap,
        )
        traversable = traversable_by_commit_index.get(entry.commit_index, 1)
        committed_route_cell_count = len(attempt_snap.committed_route_cells)
        goals_nonempty = entry.fill_first_ok and entry.probe_reachable is True
        stale_class = classify_stale_attribution(
            probe_failure_class=entry.probe_failure_class,
            commit_probe_reachable=bool(entry.probe_reachable),
            commit_conflict_reason=entry.commit_conflict_reason,
            probe_start=entry.probe_start,
            candidate_route_probe_start=candidate.route_probe_start,
            goals_nonempty_at_commit=goals_nonempty,
            global_goal_count=global_goal_count,
            committed_route_cell_count=committed_route_cell_count,
            traversable_cell_count=traversable,
            new_blocking_cells_since_last_commit_count=blocking_count,
        )
        rows.append(
            ElcpStaleAttributionRow(
                commit_index=entry.commit_index,
                candidate_id=entry.candidate_id,
                probe_failure_class=entry.probe_failure_class.value,
                stale_attribution_class=stale_class,
                commit_conflict_reason=entry.commit_conflict_reason,
                candidate_route_probe_reachable=candidate.reachable,
                commit_probe_reachable=bool(entry.probe_reachable),
                probe_start=entry.probe_start,
                candidate_route_probe_start=candidate.route_probe_start,
                committed_route_cell_count=committed_route_cell_count,
                new_blocking_cells_since_last_commit_count=blocking_count,
                new_blocking_cells_sample=blocking_sample,
                probe_expanded_nodes=entry.probe_expanded_nodes,
                probe_max_expansions=entry.max_expansions,
                domain_version=entry.domain_version,
                deferred_retry_eligible=entry.deferred_retry_eligible,
                assigned_lane_id=entry.assigned_lane_id,
                git_sha=git_sha,
            )
        )
    return tuple(rows)


def _build_traversable_by_commit_index(
    *,
    snapshots_at_attempt: Sequence[MirrorDomainSnapshot],
    inp: OptimizationInput,
    skeleton: object,
) -> dict[int, int]:
    from django_apps.asteroid_lab.optimization.commit.incremental_commit import _rebuild_domain

    out: dict[int, int] = {}
    for snap in snapshots_at_attempt:
        domain = _rebuild_domain(
            skeleton,
            inp,
            committed_occupied=snap.committed_occupied,
            committed_route_cells=snap.committed_route_cells,
        )
        out[snap.commit_index] = len(domain.traversable_cells)
    return out


def run_gate_a_elcp_d0_overlap_stale_forensics(
    *,
    imported_game_data_batch_module: object,
) -> ElcpD0ForensicsResult:
    git_sha = resolve_git_sha()
    inp, pipeline_config = build_gate_a_rf1_inputs(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    config = replace(
        pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
    )
    captured: dict[str, object] = {}
    primary_results: list[CommitResult] = []
    real_commit = incremental_commit

    def _capture_primary(*args: object, **kwargs: object) -> CommitResult:
        result = real_commit(*args, **kwargs)
        primary_results.append(result)
        captured["genome"] = args[0]
        captured["candidates_by_id"] = args[1]
        captured["inp"] = args[2]
        captured["skeleton"] = args[3]
        captured["domain"] = kwargs["domain"]
        captured["exterior_lane_plan"] = kwargs.get("exterior_lane_plan")
        captured["route_probe_start_policy"] = kwargs.get("route_probe_start_policy")
        captured["resource_kind"] = kwargs.get("resource_kind")
        return result

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        side_effect=_capture_primary,
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=config,
        )

    if not primary_results:
        msg = "primary incremental_commit was not called"
        raise AssertionError(msg)

    primary = primary_results[0]
    plan = captured["exterior_lane_plan"]
    if plan is None:
        msg = "ELCP exterior_lane_plan required for D0 Gate A"
        raise AssertionError(msg)

    genome = captured["genome"]
    candidates_by_id = captured["candidates_by_id"]
    inp_cap = captured["inp"]
    skeleton = captured["skeleton"]
    domain = captured["domain"]

    mirror = build_elcp_primary_mirror_ledger(
        genome=genome,
        candidates_by_id=candidates_by_id,
        inp=inp_cap,
        skeleton=skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
        collect_domain_snapshots=True,
    )
    assert_mirror_parity(production=primary, mirror=mirror)

    global_goal_count = len(probe_goal_coords(inp_cap, skeleton))
    traversable_by_index = _build_traversable_by_commit_index(
        snapshots_at_attempt=mirror.domain_snapshots_at_attempt,
        inp=inp_cap,
        skeleton=skeleton,
    )

    rows = build_stale_attribution_rows(
        ledger=mirror.ledger,
        snapshots_after_success=mirror.domain_snapshots_after_success,
        snapshots_at_attempt=mirror.domain_snapshots_at_attempt,
        candidates_by_id=candidates_by_id,
        global_goal_count=global_goal_count,
        traversable_by_commit_index=traversable_by_index,
        git_sha=git_sha,
    )

    histogram = dict(Counter(r.stale_attribution_class.value for r in rows))
    unattributed = histogram.get(ElcpStaleAttributionClass.UNATTRIBUTED_STALE.value, 0)
    coverage = 1.0 - (unattributed / len(rows)) if rows else 0.0
    reservation_flags = [r.commit_conflict_reason in RESERVATION_CONFLICT_REASONS for r in rows]
    verdict = compute_d0_verdict(
        attribution_classes=[r.stale_attribution_class for r in rows],
        new_blocking_cells_counts=[r.new_blocking_cells_since_last_commit_count for r in rows],
        reservation_conflict_flags=reservation_flags,
    )

    return ElcpD0ForensicsResult(
        git_sha=git_sha,
        rows=rows,
        histogram=histogram,
        verdict=verdict,
        attribution_coverage=coverage,
        unattributed_ratio=unattributed / len(rows) if rows else 1.0,
        c0_carry_forward={
            "note": "See C0 report for dual-run aggregate; D0 run is overlap-pack only",
            "overlap_commit_order_len": len(genome.commit_order),
            "overlap_primary_committed_count": len(primary.committed_ids),
            "overlap_stale_row_count": len(rows),
        },
    )
