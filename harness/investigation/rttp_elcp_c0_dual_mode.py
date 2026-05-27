"""P1-ELCP-RF-C0: Gate A dual-mode primary commit forensics (not solver input)."""

from __future__ import annotations

import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any
from unittest.mock import patch

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    CommitResult,
    incremental_commit,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpAttemptLedgerRow,
    ElcpProbeFailureClass,
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
)
from harness.investigation.rttp_elcp_reprobe_step_forensics import extract_elcp_reprobe_forensics
from harness.investigation.rttp_elcp_universe_sanity import extract_elcp_attempt_universe_sanity

GATE_A_RECOVERY_SLUG = "rttp-core-recovery-test-map"
DOMINANT_BUCKET_MIN_PCT = 0.40


@dataclass(frozen=True, slots=True)
class ElcpC0ModeRunSnapshot:
    selection_mode: str
    git_sha: str
    commit_order_len: int
    primary_committed_count: int
    primary_conflict_count: int
    primary_reprobe_failed_count: int
    lane_capacity_shortfall_count: int
    route_feasible_shortfall_count: int
    stale_candidate_reachable_count: int
    validation_passed: bool
    throughput_shortfall_reason: str | None
    bucket_coverage: float
    bucket_histogram: dict[str, int]
    dominant_bucket: str
    dominant_bucket_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection_mode": self.selection_mode,
            "git_sha": self.git_sha,
            "commit_order_len": self.commit_order_len,
            "primary_committed_count": self.primary_committed_count,
            "primary_conflict_count": self.primary_conflict_count,
            "primary_reprobe_failed_count": self.primary_reprobe_failed_count,
            "lane_capacity_shortfall_count": self.lane_capacity_shortfall_count,
            "route_feasible_shortfall_count": self.route_feasible_shortfall_count,
            "stale_candidate_reachable_count": self.stale_candidate_reachable_count,
            "validation_passed": self.validation_passed,
            "throughput_shortfall_reason": self.throughput_shortfall_reason,
            "bucket_coverage": self.bucket_coverage,
            "bucket_histogram": dict(self.bucket_histogram),
            "dominant_bucket": self.dominant_bucket,
            "dominant_bucket_pct": self.dominant_bucket_pct,
        }


def resolve_git_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _bucket_stats(
    ledger_failed: Sequence[ElcpAttemptLedgerRow],
) -> tuple[float, dict[str, int], str, float]:
    histogram = Counter(row.probe_failure_class.value for row in ledger_failed)
    if not ledger_failed:
        return 1.0, {}, "none", 0.0
    known = sum(
        1
        for row in ledger_failed
        if row.probe_failure_class is not ElcpProbeFailureClass.UNKNOWN_REPROBE_FAILED
    )
    coverage = known / len(ledger_failed)
    dominant_bucket, dominant_count = histogram.most_common(1)[0]
    dominant_pct = dominant_count / len(ledger_failed)
    return coverage, dict(histogram), dominant_bucket, dominant_pct


def _extract_throughput_shortfall_reason(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> str | None:
    for step in algorithm_steps:
        metrics = step.get("metrics")
        if isinstance(metrics, Mapping):
            reason = metrics.get("throughput_shortfall_reason")
            if isinstance(reason, str) and reason:
                return reason
        summary = step.get("summary")
        if isinstance(summary, str) and "throughput" in summary.lower():
            return summary
    return None


def build_dual_run_comparison_table(
    *,
    baseline: ElcpC0ModeRunSnapshot,
    overlap: ElcpC0ModeRunSnapshot,
) -> list[dict[str, Any]]:
    def _row(
        metric: str,
        base_val: Any,
        overlap_val: Any,
        *,
        delta: Any | None = None,
    ) -> dict[str, Any]:
        if delta is None and isinstance(base_val, int) and isinstance(overlap_val, int):
            delta = overlap_val - base_val
        return {
            "metric": metric,
            "greedy_regret": base_val,
            "greedy_regret_overlap_pack": overlap_val,
            "delta": delta,
        }

    return [
        _row("commit_order_len", baseline.commit_order_len, overlap.commit_order_len),
        _row(
            "primary_committed_count",
            baseline.primary_committed_count,
            overlap.primary_committed_count,
        ),
        _row(
            "primary_conflict_count",
            baseline.primary_conflict_count,
            overlap.primary_conflict_count,
        ),
        _row(
            "primary_reprobe_failed_count",
            baseline.primary_reprobe_failed_count,
            overlap.primary_reprobe_failed_count,
        ),
        _row(
            "lane_capacity_shortfall_count",
            baseline.lane_capacity_shortfall_count,
            overlap.lane_capacity_shortfall_count,
        ),
        _row(
            "route_feasible_shortfall_count",
            baseline.route_feasible_shortfall_count,
            overlap.route_feasible_shortfall_count,
        ),
        _row(
            "stale_candidate_reachable_count",
            baseline.stale_candidate_reachable_count,
            overlap.stale_candidate_reachable_count,
        ),
        {
            "metric": "validation_passed",
            "greedy_regret": baseline.validation_passed,
            "greedy_regret_overlap_pack": overlap.validation_passed,
            "delta": None,
            "signal_class": "informational_e2e",
        },
        {
            "metric": "throughput_shortfall_reason",
            "greedy_regret": baseline.throughput_shortfall_reason,
            "greedy_regret_overlap_pack": overlap.throughput_shortfall_reason,
            "delta": None,
            "signal_class": "informational",
        },
    ]


def derive_lane_capacity_shortfall_regate(
    *,
    baseline: ElcpC0ModeRunSnapshot,
    overlap: ElcpC0ModeRunSnapshot,
    validation_regression: bool,
) -> tuple[str, str]:
    if validation_regression:
        return (
            "BLOCKED",
            "validation_passed E2E regression on overlap-pack "
            "(informational_e2e safety veto); C0 blocked pending B1 follow-up",
        )
    committed_delta = overlap.primary_committed_count - baseline.primary_committed_count
    if overlap.dominant_bucket == ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE.value:
        if overlap.dominant_bucket_pct >= DOMINANT_BUCKET_MIN_PCT:
            return (
                "BLOCKED",
                "stale_candidate_reachable dominant on overlap-pack; "
                "lane_capacity_shortfall B-spec not appropriate",
            )
    if overlap.dominant_bucket == ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL.value:
        if overlap.dominant_bucket_pct >= DOMINANT_BUCKET_MIN_PCT:
            if committed_delta <= 1:
                return (
                    "UNBLOCKED",
                    "lane_capacity_shortfall dominant on overlap-pack with low committed lift; "
                    "Layer 2 B-spec may be drafted separately",
                )
            return (
                "NARROWED_TO_COMMIT_ORDER",
                "lane_capacity_shortfall dominant but primary_committed improved; "
                "scope commit-order universe",
            )
    if committed_delta >= 2:
        return (
            "BLOCKED",
            "primary_committed meaningfully increased; re-evaluate next bottleneck "
            "before lane_capacity_shortfall B-spec",
        )
    if baseline.commit_order_len < overlap.commit_order_len and committed_delta <= 1:
        return (
            "UNBLOCKED",
            "commit_order grew but primary_committed flat; "
            "Layer 2 lane_capacity_shortfall is primary suspect",
        )
    return (
        "BLOCKED",
        "no clear lane_capacity_shortfall dominance or committed lift; "
        "keep program B-spec blocked",
    )


def build_gate_a_rf1_inputs(
    *,
    imported_game_data_batch_module: object,
) -> tuple[OptimizationInput, RttpPipelineConfig]:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
        optimization_input_from_reconstruction,
    )
    from django_apps.asteroid_lab.reconstruction.complete_map import (
        build_reconstruction_complete_map,
    )
    from django_apps.asteroid_lab.reconstruction.field_cells import (
        asteroid_field_cell_count_for_placement,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
        build_reconstruction_capacity_envelope,
    )
    from django_apps.asteroid_lab.services.throughput_target import (
        compute_target_throughput_per_min,
        parse_throughput_target_percent,
        primary_reconstruction_max_per_min,
    )
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    _ = imported_game_data_batch_module
    project_id = import_core_recovery_test_map(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    if inp_row is None:
        msg = "recovery map AsteroidMapInput missing"
        raise AssertionError(msg)
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id="elcp-c0-post-b1-regate",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    percent = parse_throughput_target_percent({})
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=percent,
    )
    platform = asteroid_field_cell_count_for_placement(complete_map, inp.transport_kind)
    pipeline_config = RttpPipelineConfig(
        target_throughput_per_min=target,
        placement_target_percent=percent,
        placement_platform_cell_count=platform,
        reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(cap),
    )
    return inp, pipeline_config


def run_gate_a_elcp_c0_mode(
    *,
    inp: OptimizationInput,
    pipeline_config: RttpPipelineConfig,
    selection_mode: SelectionMode,
    git_sha: str,
) -> ElcpC0ModeRunSnapshot:
    config = replace(pipeline_config, selection_mode=selection_mode)
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
        pipeline_result = run_rttp_pipeline(
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
    plan = captured.get("exterior_lane_plan")
    if plan is None:
        msg = "ELCP exterior_lane_plan required for C0 Gate A"
        raise AssertionError(msg)

    mirror = build_elcp_primary_mirror_ledger(
        genome=captured["genome"],
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        skeleton=captured["skeleton"],
        domain=captured["domain"],
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
    )
    assert_mirror_parity(production=primary, mirror=mirror)

    failed = mirror.ledger
    coverage, histogram, dominant_bucket, dominant_pct = _bucket_stats(failed)
    stale_count = histogram.get(ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE.value, 0)
    reprobe_count = sum(
        1
        for conflict in primary.conflicts
        if conflict.reason is CommitConflictReason.REPROBE_FAILED
    )

    step_forensics = extract_elcp_reprobe_forensics(pipeline_result.algorithm_steps)
    assert (
        step_forensics["lane_capacity_shortfall_count"] == primary.lane_capacity_shortfall_count
    )
    assert (
        step_forensics["route_feasible_shortfall_count"] == primary.route_feasible_shortfall_count
    )

    _ = extract_elcp_attempt_universe_sanity(
        algorithm_steps=pipeline_result.algorithm_steps,
        inp=inp,
        pipeline_config=config,
        primary_commit_result=primary,
        exterior_lane_plan=plan,
    )

    genome = captured["genome"]
    assert isinstance(genome, PlacementGenome)
    commit_order_len = len(genome.commit_order)

    return ElcpC0ModeRunSnapshot(
        selection_mode=selection_mode.value,
        git_sha=git_sha,
        commit_order_len=commit_order_len,
        primary_committed_count=len(primary.committed_ids),
        primary_conflict_count=len(primary.conflicts),
        primary_reprobe_failed_count=reprobe_count,
        lane_capacity_shortfall_count=primary.lane_capacity_shortfall_count,
        route_feasible_shortfall_count=primary.route_feasible_shortfall_count,
        stale_candidate_reachable_count=stale_count,
        validation_passed=pipeline_result.validation_passed,
        throughput_shortfall_reason=_extract_throughput_shortfall_reason(
            pipeline_result.algorithm_steps
        ),
        bucket_coverage=coverage,
        bucket_histogram=histogram,
        dominant_bucket=dominant_bucket,
        dominant_bucket_pct=dominant_pct,
    )


def run_gate_a_elcp_c0_dual_mode(
    *,
    imported_game_data_batch_module: object,
) -> tuple[ElcpC0ModeRunSnapshot, ElcpC0ModeRunSnapshot, list[dict[str, Any]], str, str]:
    git_sha = resolve_git_sha()
    inp, pipeline_config = build_gate_a_rf1_inputs(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    baseline = run_gate_a_elcp_c0_mode(
        inp=inp,
        pipeline_config=pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET,
        git_sha=git_sha,
    )
    overlap = run_gate_a_elcp_c0_mode(
        inp=inp,
        pipeline_config=pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
        git_sha=git_sha,
    )
    table = build_dual_run_comparison_table(baseline=baseline, overlap=overlap)
    validation_regression = baseline.validation_passed and not overlap.validation_passed
    verdict, reason = derive_lane_capacity_shortfall_regate(
        baseline=baseline,
        overlap=overlap,
        validation_regression=validation_regression,
    )
    return baseline, overlap, table, verdict, reason


__all__ = [
    "ElcpC0ModeRunSnapshot",
    "GATE_A_RECOVERY_SLUG",
    "build_dual_run_comparison_table",
    "build_gate_a_rf1_inputs",
    "derive_lane_capacity_shortfall_regate",
    "resolve_git_sha",
    "run_gate_a_elcp_c0_dual_mode",
    "run_gate_a_elcp_c0_mode",
]
