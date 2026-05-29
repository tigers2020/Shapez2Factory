"""Lab UI run summary DTOs (read-only; never solver input)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)

_PLACEHOLDER = "—"


def _obs_field_count(obs: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obs:
            return obs[key]
    return _PLACEHOLDER


def _primary_resource_kind(raw: Any) -> str:
    if raw in (None, "", _PLACEHOLDER):
        return "shape"
    return str(raw)


def _primary_field_cell_count(obs: dict[str, Any], *, primary: str) -> Any:
    if primary == "fluid":
        return _obs_field_count(
            obs,
            "fluid_field_cell_count",
            "fluid_confirmed_cell_count",
            "asteroid_field_cell_count",
            "confirmed_cell_count",
            "mineable_cell_count",
        )
    return _obs_field_count(
        obs,
        "shape_field_cell_count",
        "shape_confirmed_cell_count",
        "asteroid_field_cell_count",
        "confirmed_cell_count",
        "mineable_cell_count",
    )


def _primary_field_cells_label(primary: str) -> str:
    if primary == "fluid":
        return "Fluid field cells"
    return "Shape field cells"


def _external_connector_label(primary: str) -> str:
    if primary == "fluid":
        return "External space pipes"
    return "External space belts"


def _section_reconstruction(obs: dict[str, Any] | None) -> dict[str, Any]:
    keys = (
        "cell_count",
        "display_cell_count",
        "primary_resource_kind",
        "field_cell_count",
        "rim_cell_count",
        "ambiguous_cell_count",
        "external_void_cell_count",
    )
    if not obs:
        return dict.fromkeys(keys, _PLACEHOLDER)
    primary = _primary_resource_kind(obs.get("primary_resource_kind"))
    return {
        "cell_count": obs.get("cell_count", _PLACEHOLDER),
        "display_cell_count": obs.get("display_cell_count", _PLACEHOLDER),
        "primary_resource_kind": primary,
        "field_cell_count": _primary_field_cell_count(obs, primary=primary),
        "rim_cell_count": obs.get("rim_cell_count", _PLACEHOLDER),
        "ambiguous_cell_count": obs.get("ambiguous_cell_count", _PLACEHOLDER),
        "external_void_cell_count": obs.get("external_void_cell_count", _PLACEHOLDER),
    }


def _parse_decimal_throughput(value: Any) -> Decimal | None:
    if value in (None, "", _PLACEHOLDER):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _external_line_count(*, max_throughput_per_min: Any, primary: str) -> int | str:
    throughput = _parse_decimal_throughput(max_throughput_per_min)
    if throughput is None:
        return _PLACEHOLDER
    if primary != "shape":
        return _PLACEHOLDER
    from django_apps.game_data.services.exterior_transport_capacity import (
        exterior_line_count_for_throughput,
    )

    try:
        return exterior_line_count_for_throughput(
            throughput,
            resource_kind=primary,
        )
    except (LookupError, ValueError):
        return _PLACEHOLDER


def _external_connector_count(
    *,
    max_throughput_per_min: Any,
    primary: str,
) -> int | str:
    throughput = _parse_decimal_throughput(max_throughput_per_min)
    if throughput is None:
        return _PLACEHOLDER
    from django_apps.game_data.services.exterior_transport_capacity import (
        exterior_connector_count_for_throughput,
    )

    try:
        return exterior_connector_count_for_throughput(
            throughput,
            resource_kind=primary,
        )
    except LookupError:
        return _PLACEHOLDER


def _section_capacity(cap: dict[str, Any] | None) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "shape_max_throughput_per_min": _PLACEHOLDER,
        "fluid_max_throughput_per_min": _PLACEHOLDER,
        "shape_output_unit": _PLACEHOLDER,
        "fluid_output_unit": _PLACEHOLDER,
        "shape_platform_count": _PLACEHOLDER,
        "fluid_platform_count": _PLACEHOLDER,
        "reconstruction_max_throughput_per_min": _PLACEHOLDER,
        "primary_resource_kind": _PLACEHOLDER,
        "primary_output_unit": _PLACEHOLDER,
        "platform_upper_bound": _PLACEHOLDER,
        "external_connector_count": _PLACEHOLDER,
        "external_line_count": _PLACEHOLDER,
    }
    if not cap:
        return empty
    by = dict(cap.get("by_resource") or {})
    shape = dict(by.get("shape") or {})
    fluid = dict(by.get("fluid") or {})
    primary = _primary_resource_kind(cap.get("primary_resource_kind"))
    shape_max = shape.get("max_throughput_per_min", _PLACEHOLDER)
    primary_row = shape if primary == "shape" else fluid
    headline_max = primary_row.get("max_throughput_per_min", _PLACEHOLDER)
    return {
        "shape_max_throughput_per_min": shape_max,
        "fluid_max_throughput_per_min": fluid.get("max_throughput_per_min", _PLACEHOLDER),
        "shape_output_unit": shape.get("output_unit", _PLACEHOLDER),
        "fluid_output_unit": fluid.get("output_unit", _PLACEHOLDER),
        "shape_platform_count": shape.get("capacity_upper_bound_platform_count", _PLACEHOLDER),
        "fluid_platform_count": fluid.get("capacity_upper_bound_platform_count", _PLACEHOLDER),
        "reconstruction_max_throughput_per_min": headline_max,
        "primary_resource_kind": primary,
        "primary_output_unit": primary_row.get("output_unit", _PLACEHOLDER),
        "platform_upper_bound": primary_row.get(
            "capacity_upper_bound_platform_count",
            _PLACEHOLDER,
        ),
        "external_connector_count": _external_connector_count(
            max_throughput_per_min=headline_max,
            primary=primary,
        ),
        "external_line_count": _external_line_count(
            max_throughput_per_min=headline_max,
            primary=primary,
        ),
    }


def _t2_policy_section_fields(summary: dict[str, Any]) -> dict[str, Any]:
    diagnostic = summary.get("diagnostic_expected_shortfall")
    t3_eligible = summary.get("t3_ops_eligible")
    return {
        "t2_policy_status": summary.get("t2_policy_status", _PLACEHOLDER),
        "t2_policy_reason": summary.get("t2_policy_reason", _PLACEHOLDER),
        "diagnostic_expected_shortfall": (
            diagnostic if isinstance(diagnostic, bool) else _PLACEHOLDER
        ),
        "t3_ops_eligible": t3_eligible if isinstance(t3_eligible, bool) else _PLACEHOLDER,
        "t3_blocked_reason": summary.get("t3_blocked_reason", _PLACEHOLDER),
        "rttp_ops_slug_class": summary.get("rttp_ops_slug_class", _PLACEHOLDER),
    }


def _section_throughput_target(summary: dict[str, Any]) -> dict[str, Any]:
    policy_fields = _t2_policy_section_fields(summary)
    keys = (
        "reconstruction_max_throughput_per_min",
        "throughput_target_percent",
        "target_throughput_per_min",
        "actual_committed_output_per_min",
        "throughput_budget_satisfied",
        "throughput_shortfall_per_min",
        "target_utilization_ratio",
        "actual_utilization_ratio",
        "budget_status",
        "throughput_target_status",
        "t2_policy_status",
        "t2_policy_reason",
        "diagnostic_expected_shortfall",
        "t3_ops_eligible",
        "t3_blocked_reason",
        "rttp_ops_slug_class",
    )
    actual = summary.get("actual_committed_output_per_min")
    target = summary.get("target_throughput_per_min")
    percent = summary.get("throughput_target_percent")
    if actual is None or target is None or percent is None:
        row = dict.fromkeys(keys, _PLACEHOLDER)
        row.update(policy_fields)
        return row
    satisfied = summary.get("throughput_budget_satisfied")
    if satisfied is True:
        budget_status = "satisfied"
    elif satisfied is False:
        budget_status = "shortfall"
    else:
        budget_status = _PLACEHOLDER
    return {
        "reconstruction_max_throughput_per_min": summary.get(
            "reconstruction_max_throughput_per_min",
            _PLACEHOLDER,
        ),
        "throughput_target_percent": percent,
        "target_throughput_per_min": target,
        "actual_committed_output_per_min": actual,
        "throughput_budget_satisfied": satisfied if satisfied is not None else _PLACEHOLDER,
        "throughput_shortfall_per_min": summary.get("throughput_shortfall_per_min", _PLACEHOLDER),
        "target_utilization_ratio": summary.get("target_utilization_ratio", _PLACEHOLDER),
        "actual_utilization_ratio": summary.get("actual_utilization_ratio", _PLACEHOLDER),
        "budget_status": budget_status,
        "throughput_target_status": summary.get("throughput_target_status", budget_status),
        **policy_fields,
    }


def _throughput_budget_satisfied_top_level(summary: dict[str, Any]) -> bool | None:
    if summary.get("actual_committed_output_per_min") is None:
        return None
    if "throughput_target_percent" not in summary:
        return None
    if "throughput_budget_satisfied" not in summary:
        return None
    return bool(summary["throughput_budget_satisfied"])


def _section_rttp(solver_summary: dict[str, Any]) -> dict[str, Any]:
    order = list(solver_summary.get("commit_order") or [])
    if not order:
        preview: str | int = _PLACEHOLDER
    elif len(order) == 1:
        preview = str(order[0])
    else:
        preview = f"{order[0]} (+{len(order) - 1})"
    actual = solver_summary.get("actual_committed_output_per_min")
    if actual is not None:
        output_status = "available"
    else:
        output_status = "pending_pr_2b"
    return {
        "confirmed_count": solver_summary.get("confirmed_count", _PLACEHOLDER),
        "validation_passed": bool(solver_summary.get("validation_passed")),
        "actual_committed_output_per_min": actual,
        "actual_output_status": output_status,
        "candidate_count": solver_summary.get("normal_candidate_count", _PLACEHOLDER),
        "commit_order_preview": preview,
    }


def _rim_route_candidate_count(
    reconstruction: dict[str, Any],
    solver_summary: dict[str, Any],
) -> Any:
    """Outer-rim field cells = mining bundle install slots (layer 3 route candidates)."""

    for source in (
        reconstruction.get("rim_cell_count"),
        (solver_summary.get("reconstruction_observability") or {}).get("rim_cell_count"),
        solver_summary.get("rim_cell_count"),
        solver_summary.get("route_candidate_count"),
    ):
        if source not in (None, "", _PLACEHOLDER):
            return source
    return _PLACEHOLDER


def _ratio_display(*, left: Any, right: Any) -> str:
    if left in (None, "", _PLACEHOLDER) and right in (None, "", _PLACEHOLDER):
        return _PLACEHOLDER
    left_text = _PLACEHOLDER if left in (None, "", _PLACEHOLDER) else str(left)
    right_text = _PLACEHOLDER if right in (None, "", _PLACEHOLDER) else str(right)
    return f"{left_text} / {right_text}"


def _layer03_route_probe_succeeded_count(solver_summary: dict[str, Any]) -> Any:
    return _obs_field_count(
        solver_summary,
        "route_probe_succeeded_count",
        "normal_candidate_count",
    )


def _layer03_route_probed_pool_count(solver_summary: dict[str, Any]) -> Any:
    return _obs_field_count(
        solver_summary,
        "normal_candidate_count",
        "route_probe_succeeded_count",
    )


def _layer04_provisional_placed_count(solver_summary: dict[str, Any]) -> Any:
    return _obs_field_count(solver_summary, "layer04_selected_count", "selected_count")


def _layer03_skip_reason_label(solver_summary: dict[str, Any]) -> str:
    raw = solver_summary.get("layer03_skip_reason")
    if raw in (None, "", "none"):
        return _PLACEHOLDER
    return str(raw)


def _format_layer03_reject_reason_counts(solver_summary: dict[str, Any]) -> str:
    raw = solver_summary.get("layer03_reject_reason_counts")
    if not raw:
        return _PLACEHOLDER
    parts: list[str] = []
    for item in raw[:3]:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            reason, count = item
            parts.append(f"{reason}: {count}")
    return "; ".join(parts) if parts else _PLACEHOLDER


def _layer04_placement_complete_label(solver_summary: dict[str, Any]) -> str:
    slugs = solver_summary.get("completed_layer_slugs")
    if not isinstance(slugs, list) or LAYER_04_RIM_BUNDLE_PLACEMENT not in slugs:
        return _PLACEHOLDER
    selected = _layer04_provisional_placed_count(solver_summary)
    if selected in (None, "", _PLACEHOLDER):
        return _PLACEHOLDER
    try:
        return "yes" if int(selected) > 0 else "no"
    except (TypeError, ValueError):
        return _PLACEHOLDER


def _highlight(label: str, value: Any) -> dict[str, str]:
    if value is None or value == "":
        text = _PLACEHOLDER
    else:
        text = str(value)
    return {"label": label, "value": text}


def _layer_outcome(
    *,
    layer_slug: str,
    stack_run_status: str | None,
    completed_layer_slugs: frozenset[str],
    failed_layer_slug: str | None,
    legacy_outcome: str,
) -> str:
    if failed_layer_slug == layer_slug:
        return "failed"
    if layer_slug in completed_layer_slugs:
        return "completed"
    if stack_run_status == "timeout_fail_closed":
        return "skipped_budget"
    if stack_run_status is not None:
        return "pending"
    return legacy_outcome


def _build_layer_summaries(
    *,
    solver_summary: dict[str, Any],
    reconstruction: dict[str, Any],
    capacity: dict[str, Any],
    rttp: dict[str, Any],
    throughput_target: dict[str, Any],
    validation_passed: bool,
    target_placement: Any,
    capacity_deficit_count: Any,
    confirmed: Any,
    issue_codes: list[str],
    first_issue_code: str | None,
    macro_commit_summary: dict[str, Any] | None,
    optimization_goal: dict[str, Any],
) -> list[dict[str, Any]]:
    stack_run_status_raw = solver_summary.get("stack_run_status")
    stack_run_status = str(stack_run_status_raw) if stack_run_status_raw not in (None, "") else None
    completed_raw = solver_summary.get("completed_layer_slugs")
    completed_layer_slugs = frozenset(
        str(s) for s in (completed_raw if isinstance(completed_raw, list) else ())
    )
    failed_raw = solver_summary.get("failed_layer_slug")
    failed_layer_slug = str(failed_raw) if failed_raw not in (None, "") else None

    rec_has_data = reconstruction.get("field_cell_count") not in (None, _PLACEHOLDER, "")
    l1_legacy = "completed" if rec_has_data else "pending"
    l5_legacy = (
        "completed"
        if validation_passed
        else "failed" if issue_codes or first_issue_code else "pending"
    )

    def outcome(slug: str, legacy: str) -> str:
        return _layer_outcome(
            layer_slug=slug,
            stack_run_status=stack_run_status,
            completed_layer_slugs=completed_layer_slugs,
            failed_layer_slug=failed_layer_slug,
            legacy_outcome=legacy,
        )

    pct = throughput_target.get("throughput_target_percent", _PLACEHOLDER)
    target_tp = throughput_target.get("target_throughput_per_min", _PLACEHOLDER)
    primary = _primary_resource_kind(capacity.get("primary_resource_kind"))
    headline = capacity.get("reconstruction_max_throughput_per_min", _PLACEHOLDER)
    field_cells_label = _primary_field_cells_label(primary)

    macro = macro_commit_summary or {}
    rim_anchor_slots = _rim_route_candidate_count(reconstruction, solver_summary)
    route_probe_succeeded = _layer03_route_probe_succeeded_count(solver_summary)
    route_probed_pool = _layer03_route_probed_pool_count(solver_summary)
    provisional_placed = _layer04_provisional_placed_count(solver_summary)

    l2_plan = solver_summary.get("exterior_connector_plan")
    l2_required = _PLACEHOLDER
    l2_planned = solver_summary.get("planned_connector_count", _PLACEHOLDER)
    if isinstance(l2_plan, dict):
        l2_required = l2_plan.get("required_connector_count", _PLACEHOLDER)
        if l2_plan.get("planned_connector_count") is not None:
            l2_planned = l2_plan.get("planned_connector_count")

    layers: list[tuple[int, str, str, str, list[dict[str, str]]]] = [
        (
            1,
            LAYER_01_RECONSTRUCTION,
            "Reconstruction",
            outcome(LAYER_01_RECONSTRUCTION, l1_legacy),
            [
                _highlight("Primary resource", reconstruction.get("primary_resource_kind")),
                _highlight(field_cells_label, reconstruction.get("field_cell_count")),
                _highlight(
                    "Max throughput",
                    headline,
                ),
            ],
        ),
        (
            2,
            LAYER_02_EXTERIOR_TRANSPORT,
            "Exterior transport",
            outcome(LAYER_02_EXTERIOR_TRANSPORT, "pending"),
            [
                _highlight("Terrain upper bound", headline),
                _highlight("Target percent", pct if pct == _PLACEHOLDER else f"{pct}%"),
                _highlight("Planning target", target_tp),
                _highlight("Required connectors", l2_required),
                _highlight(
                    "Required planned",
                    (
                        l2_plan.get("required_planned_count", _PLACEHOLDER)
                        if isinstance(l2_plan, dict)
                        else _PLACEHOLDER
                    ),
                ),
                _highlight("Planned connectors", l2_planned),
                _highlight(
                    "Reference connectors",
                    (
                        l2_plan.get("reference_connector_count", _PLACEHOLDER)
                        if isinstance(l2_plan, dict)
                        else _PLACEHOLDER
                    ),
                ),
                _highlight(
                    "Spare connectors",
                    (
                        l2_plan.get("spare_connector_count", _PLACEHOLDER)
                        if isinstance(l2_plan, dict)
                        else _PLACEHOLDER
                    ),
                ),
                _highlight(
                    "Spare planned",
                    (
                        l2_plan.get("spare_planned_count", _PLACEHOLDER)
                        if isinstance(l2_plan, dict)
                        else _PLACEHOLDER
                    ),
                ),
                _highlight(
                    "Required normal lines",
                    capacity.get("external_line_count") if primary == "shape" else _PLACEHOLDER,
                ),
                _highlight(
                    "Reference belts @100% terrain",
                    capacity.get("external_connector_count"),
                ),
                _highlight("Platform upper bound", capacity.get("platform_upper_bound")),
            ],
        ),
        (
            3,
            LAYER_03_RIM_MINING_BUNDLES,
            "Rim mining bundles",
            outcome(LAYER_03_RIM_MINING_BUNDLES, "pending"),
            [
                _highlight("Target placements", target_placement),
                _highlight("Rim anchor slots", rim_anchor_slots),
                _highlight(
                    "Direction seed attempts",
                    _obs_field_count(solver_summary, "direction_seed_attempt_count"),
                ),
                _highlight(
                    "Exterior dir candidates",
                    _obs_field_count(solver_summary, "exterior_direction_candidate_count"),
                ),
                _highlight("Route-probed pool", route_probed_pool),
                _highlight(
                    "Route probe attempts",
                    _obs_field_count(solver_summary, "route_probe_attempt_count"),
                ),
                _highlight(
                    "Field route cells",
                    _obs_field_count(solver_summary, "field_route_cell_count_total"),
                ),
                _highlight(
                    "Weighted route cost",
                    _obs_field_count(solver_summary, "weighted_route_cost_total"),
                ),
                _highlight("Route probe succeeded", route_probe_succeeded),
                _highlight(
                    "Probe succeeded / Pool",
                    _ratio_display(left=route_probe_succeeded, right=route_probed_pool),
                ),
                _highlight(
                    "Seed projection attempts",
                    _obs_field_count(
                        solver_summary,
                        "seed_projection_attempt_count",
                    ),
                ),
                _highlight(
                    "Geometry rejected",
                    _obs_field_count(
                        solver_summary,
                        "local_geometry_rejected_count",
                    ),
                ),
                _highlight(
                    "Top reject reasons",
                    _format_layer03_reject_reason_counts(solver_summary),
                ),
                _highlight("Layer skip reason", _layer03_skip_reason_label(solver_summary)),
                _highlight("Capacity deficit", capacity_deficit_count),
            ],
        ),
        (
            4,
            LAYER_04_RIM_BUNDLE_PLACEMENT,
            "Rim bundle placement",
            outcome(LAYER_04_RIM_BUNDLE_PLACEMENT, "pending"),
            [
                _highlight("Provisional placed", provisional_placed),
                _highlight(
                    "Placed / Probe succeeded",
                    _ratio_display(left=provisional_placed, right=route_probe_succeeded),
                ),
                _highlight(
                    "Overlap rejected",
                    _obs_field_count(
                        solver_summary,
                        "layer04_rejected_overlap_count",
                        "rejected_overlap_count",
                    ),
                ),
                _highlight(
                    "Overlay occupied cells",
                    _obs_field_count(
                        solver_summary,
                        "layer04_overlay_occupied_cell_count",
                        "overlay_occupied_cell_count",
                    ),
                ),
                _highlight(
                    "Provisional placement complete",
                    _layer04_placement_complete_label(solver_summary),
                ),
            ],
        ),
        (
            5,
            LAYER_05_INNER_PATTERN_FILL,
            "Inner pattern fill",
            outcome(LAYER_05_INNER_PATTERN_FILL, "pending"),
            [
                _highlight("Macro-only mode", solver_summary.get("macro_only_mode")),
                _highlight(
                    "Macro commits",
                    macro.get("committed_macro_count") if macro else _PLACEHOLDER,
                ),
                _highlight(
                    "Macro placements",
                    macro.get("placement_count") if macro else _PLACEHOLDER,
                ),
            ],
        ),
        (
            6,
            LAYER_06_COMMIT_VALIDATE,
            "Commit & validate",
            outcome(LAYER_06_COMMIT_VALIDATE, l5_legacy),
            [
                _highlight("Confirmed placements", rttp.get("confirmed_count")),
                _highlight(
                    "Validation",
                    (
                        "passed"
                        if rttp.get("validation_passed") is True
                        else "failed" if rttp.get("validation_passed") is False else _PLACEHOLDER
                    ),
                ),
                _highlight("Commit order", rttp.get("commit_order_preview")),
                _highlight(
                    "Actual output",
                    (
                        rttp.get("actual_committed_output_per_min")
                        if rttp.get("actual_output_status") == "available"
                        else _PLACEHOLDER
                    ),
                ),
                _highlight("Budget status", throughput_target.get("budget_status")),
                _highlight(
                    "Throughput shortfall",
                    (
                        throughput_target.get("throughput_shortfall_per_min")
                        if throughput_target.get("budget_status") == "shortfall"
                        else _PLACEHOLDER
                    ),
                ),
                _highlight(
                    "First issue",
                    first_issue_code if first_issue_code else _PLACEHOLDER,
                ),
            ],
        ),
    ]
    return [
        {
            "layer_index": index,
            "layer_slug": slug,
            "title": title,
            "outcome": layer_outcome,
            "highlights": highlights,
        }
        for index, slug, title, layer_outcome, highlights in layers
    ]


def lab_run_summary_from_solver_summary(
    *,
    run_id: int,
    status: str,
    solver_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build Evolution Runs / Selected Run Detail payload from persisted summary."""

    issue_codes = list(solver_summary.get("issue_codes") or [])
    issue_details = list(solver_summary.get("issue_details") or [])
    validation_passed = bool(solver_summary.get("validation_passed"))
    capacity_satisfied = bool(solver_summary.get("capacity_satisfied"))
    run_success = bool(solver_summary.get("run_success"))
    placement_capacity_satisfied = bool(solver_summary.get("placement_capacity_satisfied"))
    throughput_budget_satisfied = _throughput_budget_satisfied_top_level(solver_summary)
    diagnostic_expected_shortfall = bool(solver_summary.get("diagnostic_expected_shortfall", False))
    t3_ops_eligible_raw = solver_summary.get("t3_ops_eligible")
    t3_ops_eligible = bool(t3_ops_eligible_raw) if isinstance(t3_ops_eligible_raw, bool) else None
    confirmed = solver_summary.get("confirmed_count", _PLACEHOLDER)
    target = solver_summary.get("target_miner_bundle_count", _PLACEHOLDER)
    target_placement = solver_summary.get("target_placement_count", target)
    target_throughput = solver_summary.get("target_throughput", target)
    confirmed_throughput = solver_summary.get("confirmed_throughput", _PLACEHOLDER)
    capacity_deficit_count = solver_summary.get("capacity_deficit_count", _PLACEHOLDER)
    throughput_deficit_count = solver_summary.get("throughput_deficit_count", _PLACEHOLDER)
    algorithm_steps = list(solver_summary.get("algorithm_steps") or [])
    macro_only_mode = solver_summary.get("macro_only_mode")
    macro_commit_summary_raw = solver_summary.get("macro_commit_summary")
    macro_commit_summary = (
        dict(macro_commit_summary_raw) if isinstance(macro_commit_summary_raw, dict) else None
    )
    optimization_goal = dict(solver_summary.get("optimization_goal") or {})
    reconstruction = _section_reconstruction(solver_summary.get("reconstruction_observability"))
    capacity = _section_capacity(solver_summary.get("reconstruction_capacity"))
    rttp = _section_rttp(solver_summary)
    throughput_target = _section_throughput_target(solver_summary)
    row: dict[str, Any] = {
        "id": str(run_id),
        "status": status,
        "algorithm_steps": algorithm_steps,
        "macro_only_mode": macro_only_mode,
        "validation_passed": validation_passed,
        "capacity_satisfied": capacity_satisfied,
        "run_success": run_success,
        "placement_capacity_satisfied": placement_capacity_satisfied,
        "throughput_budget_satisfied": throughput_budget_satisfied,
        "diagnostic_expected_shortfall": diagnostic_expected_shortfall,
        "t3_ops_eligible": t3_ops_eligible,
        "t2_policy_status": solver_summary.get("t2_policy_status"),
        "target_miner_bundle_count": target,
        "target_placement_count": target_placement,
        "target_throughput": target_throughput,
        "confirmed_throughput": confirmed_throughput,
        "capacity_deficit_count": capacity_deficit_count,
        "throughput_deficit_count": throughput_deficit_count,
        "issue_codes": issue_codes,
        "first_issue_code": issue_codes[0] if issue_codes else None,
        "first_issue_detail": issue_details[0] if issue_details else None,
        "score": confirmed,
        "miners": confirmed,
        "placed": confirmed,
        "saturation": _PLACEHOLDER,
        "cost": _PLACEHOLDER,
        "belts": _PLACEHOLDER,
        "pipes": _PLACEHOLDER,
        "extension_cap": _PLACEHOLDER,
        "reconstruction": reconstruction,
        "capacity": capacity,
        "rttp": rttp,
        "throughput_target": throughput_target,
        "throughput_goal": dict(solver_summary.get("throughput_goal") or {}),
        "optimization_goal": optimization_goal,
        "run_status": solver_summary.get("run_status"),
        "structural_validation_passed": solver_summary.get("structural_validation_passed"),
        "stack_run_status": solver_summary.get("stack_run_status", _PLACEHOLDER),
        "layer_summaries": _build_layer_summaries(
            solver_summary=solver_summary,
            reconstruction=reconstruction,
            capacity=capacity,
            rttp=rttp,
            throughput_target=throughput_target,
            validation_passed=validation_passed,
            target_placement=target_placement,
            capacity_deficit_count=capacity_deficit_count,
            confirmed=confirmed,
            issue_codes=issue_codes,
            first_issue_code=issue_codes[0] if issue_codes else None,
            macro_commit_summary=macro_commit_summary,
            optimization_goal=optimization_goal,
        ),
    }
    if macro_commit_summary:
        row["macro_commit_summary"] = macro_commit_summary
    return row


def lab_run_summary_from_orm(run: m.SolverRun) -> dict[str, Any]:
    """Serialize one :class:`SolverRun` for Lab template/JSON."""

    config = dict(run.config_json or {})
    summary = dict(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY) or {})
    status = run.status
    if status == m.SolverRun.RunStatus.COMPLETED:
        ui_status = "completed"
    elif status == m.SolverRun.RunStatus.PARTIAL:
        ui_status = "partial"
    elif status == m.SolverRun.RunStatus.FAILED:
        ui_status = "failed"
    else:
        ui_status = str(status)
    return lab_run_summary_from_solver_summary(
        run_id=int(run.pk),
        status=ui_status,
        solver_summary=summary,
    )


def solver_runs_for_lab_project(project_id: int, *, limit: int = 10) -> list[dict[str, Any]]:
    """Latest solver runs for one project (newest first)."""

    qs = m.SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id")[
        :limit
    ]
    return [lab_run_summary_from_orm(run) for run in qs]


__all__ = [
    "lab_run_summary_from_orm",
    "lab_run_summary_from_solver_summary",
    "solver_runs_for_lab_project",
]
