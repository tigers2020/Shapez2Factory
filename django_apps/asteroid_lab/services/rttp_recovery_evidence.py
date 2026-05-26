"""Extract RTTP core recovery evidence from solver output (read-only; not algorithm input)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_COMMIT_STEP_ID,
    evaluate_t3_certification,
)
from django_apps.asteroid_lab.contracts.rttp_recovery_evidence import EVIDENCE_SCHEMA_VERSION
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.rttp_recovery_stage_diagnosis import (
    diagnose_recovery_evidence_row,
)
from django_apps.asteroid_lab.services.rttp_route_connectivity import (
    count_exterior_connected_route_cells,
)

# Re-export for tests and capture command (implementation lives in rttp_route_connectivity).
__all__ = [
    "build_recovery_evidence_report",
    "build_recovery_evidence_row",
    "count_exterior_connected_route_cells",
    "evaluate_gate_a_from_row",
    "extract_overlay_connectivity_metrics",
]

_FOT_OVERLAY_KINDS = frozenset(
    {
        "placement.confirmed_fixed_output_transport",
        "placement.selected_fixed_output_transport",
        "placement.candidate_fixed_output_transport",
    }
)
_ROUTE_OVERLAY_KINDS = frozenset({"route.committed_path"})
_TRUNK_OVERLAY_KINDS = frozenset({"route_domain.preferred"})


def _pipeline_step_by_id(
    pipeline_steps: Sequence[Mapping[str, Any]],
    step_id: str,
) -> Mapping[str, Any] | None:
    for step in pipeline_steps:
        if str(step.get("step_id")) == step_id:
            return step
    return None


def _commit_metrics(pipeline_steps: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    commit_step = _pipeline_step_by_id(pipeline_steps, RTTP_COMMIT_STEP_ID)
    if commit_step is None:
        return {}
    metrics = commit_step.get("metrics")
    if isinstance(metrics, Mapping):
        return metrics
    return {}


def _overlay_cells(overlay: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not overlay:
        return []
    raw = overlay.get("cells")
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, Mapping)]


def _coords_matching_kinds(
    cells: Sequence[Mapping[str, Any]],
    *,
    kinds: frozenset[str],
) -> frozenset[Coord]:
    out: set[Coord] = set()
    for row in cells:
        kind = str(row.get("overlay_semantic_kind") or row.get("kind") or "")
        if kind not in kinds:
            continue
        out.add((int(row["x"]), int(row["y"])))
    return frozenset(out)


def extract_overlay_connectivity_metrics(
    *,
    commit_overlay: Mapping[str, Any] | None,
    route_domain_overlay: Mapping[str, Any] | None,
) -> dict[str, int]:
    commit_cells = _overlay_cells(commit_overlay)
    trunk_cells = _coords_matching_kinds(
        _overlay_cells(route_domain_overlay),
        kinds=_TRUNK_OVERLAY_KINDS,
    )
    route_cells = _coords_matching_kinds(commit_cells, kinds=_ROUTE_OVERLAY_KINDS)
    fot_cells = _coords_matching_kinds(commit_cells, kinds=_FOT_OVERLAY_KINDS)
    return {
        "committed_output_transport_cells": len(fot_cells),
        "committed_route_cell_count": len(route_cells),
        "exterior_connected_route_count": count_exterior_connected_route_cells(
            route_cells,
            trunk_cells,
        ),
        "trunk_mask_cell_count_overlay": len(trunk_cells),
    }


def load_replay_overlay_connectivity(
    *,
    project_id: int,
    run_key: str,
) -> dict[str, int]:
    """Load commit + route-domain overlays from persisted replay (output-only read)."""

    from django_apps.asteroid_lab import models as m

    track = (
        m.ReplayTrack.objects.filter(
            project_id=int(project_id),
            track_key=rttp_optimization_track_key(str(run_key)),
        )
        .first()
    )
    if track is None:
        return {
            "committed_output_transport_cells": 0,
            "committed_route_cell_count": 0,
            "exterior_connected_route_count": 0,
            "trunk_mask_cell_count_overlay": 0,
        }

    commit_overlay: dict[str, Any] | None = None
    route_domain_overlay: dict[str, Any] | None = None
    for frame in track.frames.order_by("frame_index"):
        payload = frame.frame_payload if isinstance(frame.frame_payload, Mapping) else {}
        event_type = str(payload.get("event_type") or "")
        overlay = frame.cell_overlay_json if isinstance(frame.cell_overlay_json, Mapping) else {}
        if event_type == et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT:
            commit_overlay = dict(overlay)
        elif event_type == et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT:
            route_domain_overlay = dict(overlay)

    return extract_overlay_connectivity_metrics(
        commit_overlay=commit_overlay,
        route_domain_overlay=route_domain_overlay,
    )


def build_recovery_evidence_row(
    *,
    slug: str,
    project_id: int,
    solver_run_id: int | None,
    run_key: str | None,
    solver_summary: Mapping[str, Any],
    reserved_route_cells: frozenset[Coord] | None = None,
    trunk_mask_cells: frozenset[Coord] | None,
    replay_overlay_metrics: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    steps = list(solver_summary.get("algorithm_steps") or [])
    commit_metrics = _commit_metrics(steps)
    committed_ids = commit_metrics.get("committed_ids") or []
    if not isinstance(committed_ids, list):
        committed_ids = list(committed_ids)

    capacity = solver_summary.get("reconstruction_capacity")
    shape_field_count: int | None = None
    if isinstance(capacity, Mapping):
        raw = capacity.get("shape_field_cell_count")
        if raw is not None:
            shape_field_count = int(raw)
    if shape_field_count is None:
        recon_step = _pipeline_step_by_id(steps, "reconstruction")
        if recon_step is not None:
            recon_metrics = recon_step.get("metrics")
            if isinstance(recon_metrics, Mapping):
                raw_cells = recon_metrics.get("shape_field_cell_count")
                if raw_cells is None:
                    raw_cells = recon_metrics.get("cell_count")
                if raw_cells is not None:
                    shape_field_count = int(raw_cells)

    placement_goal = solver_summary.get("placement_goal_plan")
    if not isinstance(placement_goal, Mapping):
        throughput_goal = solver_summary.get("throughput_goal")
        if isinstance(throughput_goal, Mapping):
            placement_goal = throughput_goal
    placement_goal_count: int | None = None
    asteroid_field_cell_count: int | None = None
    placement_target_percent: int | None = None
    route_feasible_candidate_cap: int | None = None
    non_overlapping_anchor_cap: int | None = None
    if isinstance(placement_goal, Mapping):
        raw_goal = placement_goal.get("placement_goal_count")
        if raw_goal is not None:
            placement_goal_count = int(raw_goal)
        raw_fields = placement_goal.get("asteroid_field_cell_count")
        if raw_fields is None:
            raw_fields = placement_goal.get("mineable_platform_cell_count")
        if raw_fields is not None:
            asteroid_field_cell_count = int(raw_fields)
        raw_percent = placement_goal.get("placement_target_percent")
        if raw_percent is not None:
            placement_target_percent = int(raw_percent)
        raw_route = placement_goal.get("route_feasible_candidate_cap")
        if raw_route is not None:
            route_feasible_candidate_cap = int(raw_route)
        raw_anchor = placement_goal.get("non_overlapping_anchor_cap")
        if raw_anchor is not None:
            non_overlapping_anchor_cap = int(raw_anchor)

    overlay = dict(replay_overlay_metrics or {})
    route_count = int(overlay.get("committed_route_cell_count", 0))
    fot_count = int(overlay.get("committed_output_transport_cells", 0))
    exterior_count = int(overlay.get("exterior_connected_route_count", 0))

    if reserved_route_cells is not None and route_count == 0:
        route_count = len(reserved_route_cells)
    if trunk_mask_cells is not None and exterior_count == 0 and route_count > 0:
        exterior_count = count_exterior_connected_route_cells(
            frozenset(reserved_route_cells or ()),
            trunk_mask_cells,
        )

    cert = evaluate_t3_certification(
        slug=slug,
        solver_summary=solver_summary,
        pipeline_steps=steps,
    )

    row: dict[str, Any] = {
        "slug": slug,
        "project_id": project_id,
        "solver_run_id": solver_run_id,
        "run_key": run_key,
        "validation_passed": bool(solver_summary.get("validation_passed")),
        "issue_codes": list(solver_summary.get("issue_codes") or []),
        "confirmed_count": int(solver_summary.get("confirmed_count") or 0),
        "committed_extractor_count": len(committed_ids),
        "visible_miner_cell_count": int(commit_metrics.get("visible_miner_cell_count") or 0),
        "visible_extension_cell_count": int(
            commit_metrics.get("visible_extension_cell_count") or 0
        ),
        "installable_shape_field_cell_count": shape_field_count,
        "placement_goal_count": placement_goal_count,
        "asteroid_field_cell_count": asteroid_field_cell_count,
        "placement_target_percent": placement_target_percent,
        "route_feasible_candidate_cap": route_feasible_candidate_cap,
        "non_overlapping_anchor_cap": non_overlapping_anchor_cap,
        "committed_output_transport_cells": fot_count,
        "committed_route_cell_count": route_count,
        "exterior_connected_route_count": exterior_count,
        "trunk_mask_cell_count_overlay": int(overlay.get("trunk_mask_cell_count_overlay", 0)),
        "cert_status": cert.cert_status,
        "t0_passed": cert.t0_pass,
        "t1a_passed": cert.t1a_pass,
        "t1b_passed": cert.t1b_pass,
        "t2_passed": cert.t2_pass,
        "t3_shell_passed": cert.t3_shell_pass,
        "slug_class": cert.slug_class,
        "normal_candidate_count": int(solver_summary.get("normal_candidate_count") or 0)
        if solver_summary.get("normal_candidate_count") is not None
        else None,
        "gate_a_passed": False,
    }
    row["gate_a_passed"] = evaluate_gate_a_from_row(row)
    stage = diagnose_recovery_evidence_row(row)
    row.update(stage.as_dict())
    # Back-compat alias for markdown tables written during A0.
    row["first_failing_stage_hint"] = row["first_failing_stage"]
    return row


def evaluate_gate_a_from_row(row: Mapping[str, Any]) -> bool:
    return (
        int(row.get("committed_extractor_count") or 0) > 0
        and int(row.get("committed_output_transport_cells") or 0) > 0
        and int(row.get("committed_route_cell_count") or 0) > 0
        and int(row.get("exterior_connected_route_count") or 0) > 0
        and bool(row.get("validation_passed"))
    )


def build_recovery_evidence_report(
    results: Sequence[Mapping[str, Any]],
    *,
    captured_at: str | None = None,
    notes: Sequence[str] | None = None,
) -> dict[str, Any]:
    when = captured_at or datetime.now(UTC).isoformat()
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "captured_at": when,
        "candidate_count": len(results),
        "gate_a_primary_pass_count": sum(1 for row in results if row.get("gate_a_passed")),
        "notes": list(notes or ()),
        "results": [dict(row) for row in results],
    }
