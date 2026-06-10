"""Lab UI run summary DTOs (read-only; never solver input)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_04_TRANSPORT_ROUTING,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
    resolve_canonical_layer_slug,
)

_PLACEHOLDER = "—"
_LAYER_SUMMARY_COMPLETED_OUTCOMES = frozenset({"completed", "superseded"})
_LAB_ENUM_LABELS: dict[str, str] = {
    "no_route_goals": "No route goals",
    "no_feasible_connector_sites": "No feasible connector sites",
    "insufficient_connector_sites": "Insufficient connector sites",
    "capacity_overflow": "Capacity overflow",
    "none": "—",
}
_ENUM_VALUE_LABELS = frozenset(
    {
        "Unmet reason",
        "Layer skip reason",
        "Failure reasons",
        "Budget status",
        "Transport kind",
        "Top reject reasons",
    }
)


def _field_cell_counts_from_capacity(capacity: dict[str, Any] | None) -> tuple[Any, Any]:
    """Read shape/fluid platform counts from CLI ``reconstruction_capacity`` envelope."""

    if not isinstance(capacity, dict):
        return None, None
    shape_cells = capacity.get("shape_field_cell_count")
    fluid_cells = capacity.get("fluid_field_cell_count")
    if shape_cells is None and fluid_cells is None:
        by_resource = capacity.get("confirmed_platforms_by_resource")
        if isinstance(by_resource, dict):
            shape_cells = by_resource.get("shape")
            fluid_cells = by_resource.get("fluid")
    return shape_cells, fluid_cells


def _resolved_completed_layer_slugs(solver_summary: dict[str, Any]) -> frozenset[str]:
    """Merge top-level stack slugs with per-layer CLI outcomes for Lab cards."""

    slugs: set[str] = set()
    raw = solver_summary.get("completed_layer_slugs")
    if isinstance(raw, list):
        slugs.update(str(item) for item in raw if item)
    for item in solver_summary.get("layer_summaries") or []:
        if not isinstance(item, dict):
            continue
        slug = str(item.get("layer_slug") or "")
        if not slug:
            continue
        if str(item.get("outcome") or "") in _LAYER_SUMMARY_COMPLETED_OUTCOMES:
            slugs.add(slug)
    rec = solver_summary.get("reconstruction_observability")
    if isinstance(rec, dict) and rec.get("field_cell_count") not in (None, 0, ""):
        slugs.add(LAYER_01_RECONSTRUCTION)
    shape_cells, fluid_cells = _field_cell_counts_from_capacity(
        solver_summary.get("reconstruction_capacity")
        if isinstance(solver_summary.get("reconstruction_capacity"), dict)
        else None
    )
    if shape_cells not in (None, 0, "") or fluid_cells not in (None, 0, ""):
        slugs.add(LAYER_01_RECONSTRUCTION)
    capacity = solver_summary.get("reconstruction_capacity")
    if isinstance(capacity, dict):
        by_resource = capacity.get("by_resource")
        if isinstance(by_resource, dict):
            for resource_row in by_resource.values():
                if not isinstance(resource_row, dict):
                    continue
                max_tp = resource_row.get("max_throughput_per_min")
                if max_tp not in (None, "", _PLACEHOLDER, 0):
                    slugs.add(LAYER_01_RECONSTRUCTION)
                    break
    return frozenset(slugs)


def validation_passed_from_solver_summary(solver_summary: dict[str, Any]) -> bool:
    """Resolve UI validation flag; CLI summaries may omit the key when stack succeeded."""

    raw = solver_summary.get("validation_passed")
    if raw is not None:
        return bool(raw)
    return bool(solver_summary.get("run_success"))


def _layer_metrics_by_slug(solver_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index CLI artifact ``layer_summaries`` metrics by ``layer_slug``."""

    indexed: dict[str, dict[str, Any]] = {}
    raw = solver_summary.get("layer_summaries")
    if not isinstance(raw, list):
        return indexed
    for item in raw:
        if not isinstance(item, dict):
            continue
        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            continue
        slug = str(item.get("layer_slug") or "")
        if slug:
            indexed[slug] = dict(metrics)
    return indexed


def solver_summary_for_lab_display(solver_summary: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested CLI layer metrics into top-level keys the Lab cards expect."""

    merged = dict(solver_summary)
    by_slug = _layer_metrics_by_slug(solver_summary)

    l2 = by_slug.get(LAYER_02_EXTERIOR_TRANSPORT, {})
    if l2 and not isinstance(merged.get("exterior_connector_plan"), dict):
        merged["exterior_connector_plan"] = dict(l2)
        merged.setdefault("planned_connector_count", l2.get("planned_connector_count"))

    l3 = by_slug.get(LAYER_03_RIM_GREEDY_PLACEMENT, {})
    if l3:
        merged.setdefault("rim_anchor_count", l3.get("rim_anchor_count"))
        merged.setdefault(
            "rim_greedy_committed_count",
            l3.get("committed_placement_count"),
        )
        merged.setdefault(
            "rim_greedy_rejected_count",
            l3.get("rejected_attempt_count"),
        )
        merged.setdefault("rim_greedy_winning_variant_id", l3.get("winning_variant_id"))
        merged.setdefault("rim_greedy_pass2_score", l3.get("pass2_score"))
        merged.setdefault("layer03_skip_reason", l3.get("layer_skip_reason"))
        merged.setdefault(
            "route_feasible_rim_anchor_count",
            l3.get("route_feasible_rim_anchor_count"),
        )
        merged.setdefault("rim_anchor_fill_ratio", l3.get("rim_anchor_fill_ratio"))
        merged.setdefault(
            "rim_greedy_reserved_route_cells",
            l3.get("reserved_route_cell_count"),
        )
        merged.setdefault("layer03_reject_reason_counts", l3.get("reject_reason_counts"))

    l4_inner = by_slug.get(LAYER_04_INNER_PATTERN_FILL, {})
    if l4_inner:
        merged.setdefault(
            "interior_occupied_cell_count",
            l4_inner.get("interior_occupied_cell_count"),
        )
        merged.setdefault("interior_candidate_count", l4_inner.get("interior_candidate_count"))
        merged.setdefault("coverage_ratio", l4_inner.get("coverage_ratio"))
        merged.setdefault(
            "layer04_skip_reason",
            l4_inner.get("layer_skip_reason") or l4_inner.get("skip_reason"),
        )
        merged.setdefault("layer04_budget_interrupted", l4_inner.get("budget_interrupted"))

    if LAYER_05_TRANSPORT_ROUTING in by_slug:
        l5_transport = by_slug[LAYER_05_TRANSPORT_ROUTING]
    elif LAYER_04_TRANSPORT_ROUTING in by_slug:
        l5_transport = by_slug[LAYER_04_TRANSPORT_ROUTING]
    else:
        l5_transport = {}
    if l5_transport:
        merged.setdefault("layer04_source_count", l5_transport.get("source_count"))
        merged.setdefault("layer04_routed_source_count", l5_transport.get("routed_source_count"))
        merged.setdefault("layer04_failed_source_count", l5_transport.get("failed_source_count"))
        merged.setdefault("layer04_route_count", l5_transport.get("route_count"))
        merged.setdefault("layer04_group_count", l5_transport.get("group_count"))
        merged.setdefault("layer04_transport_tile_count", l5_transport.get("transport_tile_count"))
        merged.setdefault("layer04_total_route_cells", l5_transport.get("total_route_cells"))
        merged.setdefault("layer04_transport_kind", l5_transport.get("transport_kind"))
        if l5_transport.get("failure_reasons") is not None:
            merged.setdefault("layer04_failure_reasons", l5_transport.get("failure_reasons"))

    return merged


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


def _section_reconstruction(
    obs: dict[str, Any] | None,
    capacity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    keys = (
        "cell_count",
        "display_cell_count",
        "primary_resource_kind",
        "field_cell_count",
        "rim_cell_count",
        "ambiguous_cell_count",
        "external_void_cell_count",
    )
    if obs:
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
    shape_cells, fluid_cells = _field_cell_counts_from_capacity(capacity)
    if shape_cells not in (None, 0, "") or fluid_cells not in (None, 0, ""):
        primary = _primary_resource_kind(
            capacity.get("primary_resource_kind") if isinstance(capacity, dict) else None
        )
        field_count = fluid_cells if primary == "fluid" else shape_cells
        return {
            "cell_count": _PLACEHOLDER,
            "display_cell_count": _PLACEHOLDER,
            "primary_resource_kind": primary,
            "field_cell_count": field_count,
            "rim_cell_count": _PLACEHOLDER,
            "ambiguous_cell_count": _PLACEHOLDER,
            "external_void_cell_count": _PLACEHOLDER,
        }
    return dict.fromkeys(keys, _PLACEHOLDER)


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


def _rttp_validation_passed_tri_state(solver_summary: dict[str, Any]) -> bool | None:
    """Tri-state validation for L6 highlights (None = unknown, not failed)."""

    if "validation_passed" in solver_summary:
        return bool(solver_summary.get("validation_passed"))
    if "run_success" in solver_summary:
        return bool(solver_summary.get("run_success"))
    return None


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
        "validation_passed": _rttp_validation_passed_tri_state(solver_summary),
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


def _rim_greedy_summary_active(solver_summary: dict[str, Any]) -> bool:
    if "rim_greedy_winning_variant_id" in solver_summary:
        return True
    if LAYER_03_RIM_GREEDY_PLACEMENT in _resolved_completed_layer_slugs(solver_summary):
        return True
    for item in solver_summary.get("layer_summaries") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("layer_slug") or "") == LAYER_03_RIM_GREEDY_PLACEMENT:
            return True
    return False


def _is_absent_highlight_value(value: Any) -> bool:
    if value in (None, "", _PLACEHOLDER):
        return True
    text = str(value).strip().lower()
    if text in {"", "none", "false", "no"}:
        return True
    return False


def _append_meaningful_highlight(
    rows: list[dict[str, str]],
    label: str,
    value: Any,
    *,
    allow_zero: bool = False,
) -> None:
    if not allow_zero and _is_absent_highlight_value(value):
        return
    if not allow_zero:
        try:
            if Decimal(str(value)) == 0:
                return
        except (InvalidOperation, ValueError, TypeError):
            pass
    rows.append(_highlight(label, value))


def _visible_highlights(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("value") not in (None, "", _PLACEHOLDER)]


def _format_coverage_ratio(value: Any) -> str:
    if _is_absent_highlight_value(value):
        return _PLACEHOLDER
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        return str(value)
    if ratio <= 1.0:
        return f"{ratio * 100:.1f}%"
    return f"{ratio:.1f}%"


def _layer04_failure_reasons_label(solver_summary: dict[str, Any]) -> str:
    raw = _obs_field_count(solver_summary, "layer04_failure_reasons", "failure_reasons")
    if isinstance(raw, list):
        parts = [str(item) for item in raw if item not in (None, "")]
        return "; ".join(parts) if parts else _PLACEHOLDER
    return str(raw) if raw not in (None, _PLACEHOLDER) else _PLACEHOLDER


def _layer04_transport_highlights(solver_summary: dict[str, Any]) -> list[dict[str, str]]:
    source_count = _obs_field_count(solver_summary, "layer04_source_count", "source_count")
    routed = _obs_field_count(
        solver_summary,
        "layer04_routed_source_count",
        "routed_source_count",
    )
    return [
        _highlight(
            "Transport kind",
            _obs_field_count(solver_summary, "layer04_transport_kind", "transport_kind"),
        ),
        _highlight(
            "Sources routed",
            _ratio_display(left=routed, right=source_count),
        ),
        _highlight(
            "Transport tiles",
            _obs_field_count(
                solver_summary,
                "layer04_transport_tile_count",
                "transport_tile_count",
            ),
        ),
        _highlight(
            "Routes / groups",
            _ratio_display(
                left=_obs_field_count(solver_summary, "layer04_route_count", "route_count"),
                right=_obs_field_count(solver_summary, "layer04_group_count", "group_count"),
            ),
        ),
        _highlight(
            "Route cells",
            _obs_field_count(
                solver_summary,
                "layer04_total_route_cells",
                "total_route_cells",
            ),
        ),
        _highlight(
            "Failed sources",
            _obs_field_count(
                solver_summary,
                "layer04_failed_source_count",
                "failed_source_count",
            ),
        ),
        _highlight("Failure reasons", _layer04_failure_reasons_label(solver_summary)),
    ]


def _layer03_greedy_highlights(solver_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    _append_meaningful_highlight(
        rows,
        "Rim anchor slots",
        _obs_field_count(solver_summary, "rim_anchor_count"),
        allow_zero=True,
    )
    _append_meaningful_highlight(
        rows,
        "Route-feasible rim slots",
        _obs_field_count(solver_summary, "route_feasible_rim_anchor_count"),
    )
    committed = _obs_field_count(
        solver_summary,
        "rim_greedy_committed_count",
        "normal_candidate_count",
    )
    _append_meaningful_highlight(rows, "Committed placements", committed, allow_zero=True)
    fill_ratio = _obs_field_count(solver_summary, "rim_anchor_fill_ratio")
    if fill_ratio not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Rim fill ratio", _format_coverage_ratio(fill_ratio)))
    skip_reason = _layer03_skip_reason_label(solver_summary)
    if skip_reason not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Layer skip reason", skip_reason))
    _append_meaningful_highlight(
        rows,
        "Rejected attempts",
        _obs_field_count(
            solver_summary,
            "rim_greedy_rejected_count",
            "route_probe_failed_count",
        ),
    )
    reject_summary = _format_layer03_reject_reason_counts(solver_summary)
    if reject_summary not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Top reject reasons", reject_summary))
    _append_meaningful_highlight(
        rows,
        "Winning variant",
        _obs_field_count(solver_summary, "rim_greedy_winning_variant_id"),
    )
    _append_meaningful_highlight(
        rows,
        "Pass2 score",
        _obs_field_count(solver_summary, "rim_greedy_pass2_score"),
    )
    _append_meaningful_highlight(
        rows,
        "Reserved route cells",
        _obs_field_count(
            solver_summary,
            "rim_greedy_reserved_route_cells",
            "field_route_cell_count_total",
        ),
    )
    return _visible_highlights(rows)


def _layer03_legacy_highlights(
    solver_summary: dict[str, Any],
    *,
    target_placement: Any,
    rim_anchor_slots: Any,
    route_probed_pool: Any,
    route_probe_succeeded: Any,
    capacity_deficit_count: Any,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    _append_meaningful_highlight(rows, "Target placements", target_placement, allow_zero=True)
    _append_meaningful_highlight(rows, "Rim anchor slots", rim_anchor_slots, allow_zero=True)
    probe_ratio = _ratio_display(left=route_probe_succeeded, right=route_probed_pool)
    if probe_ratio not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Probe succeeded / pool", probe_ratio))
    skip_reason = _layer03_skip_reason_label(solver_summary)
    if skip_reason not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Layer skip reason", skip_reason))
    _append_meaningful_highlight(rows, "Route probe succeeded", route_probe_succeeded)
    _append_meaningful_highlight(
        rows,
        "Geometry rejected",
        _obs_field_count(solver_summary, "local_geometry_rejected_count"),
    )
    reject_summary = _format_layer03_reject_reason_counts(solver_summary)
    if reject_summary not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Top reject reasons", reject_summary))
    _append_meaningful_highlight(rows, "Capacity deficit", capacity_deficit_count)
    return _visible_highlights(rows)


def _layer04_inner_fill_highlights(solver_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    _append_meaningful_highlight(
        rows,
        "Interior occupied cells",
        _obs_field_count(solver_summary, "interior_occupied_cell_count"),
        allow_zero=True,
    )
    coverage = _obs_field_count(solver_summary, "coverage_ratio")
    if coverage not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Coverage ratio", _format_coverage_ratio(coverage)))
    _append_meaningful_highlight(
        rows,
        "Interior candidates",
        _obs_field_count(solver_summary, "interior_candidate_count"),
    )
    skip_reason = solver_summary.get("layer04_skip_reason")
    if skip_reason not in (None, "", _PLACEHOLDER, "none"):
        rows.append(_highlight("Layer skip reason", skip_reason))
    if solver_summary.get("layer04_budget_interrupted") is True:
        rows.append(_highlight("Budget status", "Interrupted"))
    return _visible_highlights(rows)


def _layer04_rim_bundle_highlights(
    solver_summary: dict[str, Any],
    *,
    provisional_placed: Any,
    route_probe_succeeded: Any,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    _append_meaningful_highlight(rows, "Provisional placed", provisional_placed, allow_zero=True)
    placed_ratio = _ratio_display(left=provisional_placed, right=route_probe_succeeded)
    if placed_ratio not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Placed / probe succeeded", placed_ratio))
    _append_meaningful_highlight(
        rows,
        "Overlap rejected",
        _obs_field_count(
            solver_summary,
            "layer04_rejected_overlap_count",
            "rejected_overlap_count",
        ),
    )
    complete = _layer04_placement_complete_label(solver_summary)
    if complete not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Placement complete", complete))
    return _visible_highlights(rows)


def _format_layer03_reject_reason_counts(solver_summary: dict[str, Any]) -> str:
    raw = solver_summary.get("layer03_reject_reason_counts")
    if not raw:
        return _PLACEHOLDER
    parts: list[str] = []
    for item in raw[:3]:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            reason, count = item
            parts.append(f"{_format_snake_case_label(str(reason))}: {count}")
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


def _format_compact_number(value: Any) -> str:
    if value in (None, "", _PLACEHOLDER):
        return _PLACEHOLDER
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    if number == number.to_integral_value():
        return format(int(number), ",")
    normalized = number.normalize()
    text = format(normalized, "f").rstrip("0").rstrip(".")
    return text or "0"


def _format_snake_case_label(value: str) -> str:
    key = value.strip().lower()
    if not key or key == "none":
        return _PLACEHOLDER
    mapped = _LAB_ENUM_LABELS.get(key)
    if mapped is not None:
        return mapped
    return value.replace("_", " ")


def _format_highlight_value(label: str, value: Any) -> str:
    if value is None or value == "":
        return _PLACEHOLDER
    if label in _ENUM_VALUE_LABELS:
        if isinstance(value, list):
            parts = [
                _format_snake_case_label(str(item)) for item in value if item not in (None, "")
            ]
            return "; ".join(parts) if parts else _PLACEHOLDER
        return _format_snake_case_label(str(value))
    if label.endswith("throughput") or "throughput" in label.lower():
        compact = _format_compact_number(value)
        if compact != _PLACEHOLDER:
            return compact
    if isinstance(value, (int, float, Decimal)):
        return _format_compact_number(value)
    text = str(value)
    if text.replace(".", "", 1).replace("-", "", 1).isdigit():
        return _format_compact_number(text)
    return text


def _highlight(label: str, value: Any) -> dict[str, str]:
    return {"label": label, "value": _format_highlight_value(label, value)}


def _superseded_status_label(layer_slug: str) -> str:
    if layer_slug == LAYER_04_RIM_BUNDLE_PLACEMENT:
        return "Replaced by rim greedy placement (L3)"
    if layer_slug in {LAYER_04_TRANSPORT_ROUTING, LAYER_05_INNER_PATTERN_FILL}:
        return "Replaced by current stack numbering"
    return "Superseded by active stack path"


def _cli_layer_outcome(solver_summary: dict[str, Any], layer_slug: str) -> str | None:
    for item in solver_summary.get("layer_summaries") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("layer_slug") or "") != layer_slug:
            continue
        outcome = str(item.get("outcome") or "")
        if outcome in {"superseded", "skipped_budget", "failed", "completed"}:
            return outcome
    return None


def _layer02_transport_highlights(
    *,
    pct: Any,
    target_tp: Any,
    l2_required: Any,
    l2_planned: Any,
    l2_plan: dict[str, Any] | None,
    capacity: dict[str, Any],
    primary: str,
) -> list[dict[str, str]]:
    shortfall = (
        l2_plan.get("connector_shortfall_count", _PLACEHOLDER)
        if isinstance(l2_plan, dict)
        else _PLACEHOLDER
    )
    unmet = l2_plan.get("unmet_reason", _PLACEHOLDER) if isinstance(l2_plan, dict) else _PLACEHOLDER
    candidate_slots = (
        l2_plan.get("candidate_slot_count", _PLACEHOLDER)
        if isinstance(l2_plan, dict)
        else _PLACEHOLDER
    )
    rows: list[dict[str, str]] = [
        _highlight("Target percent", pct if pct == _PLACEHOLDER else f"{pct}%"),
        _highlight("Planning target", target_tp),
        _highlight("Required connectors", l2_required),
        _highlight("Planned connectors", l2_planned),
    ]
    if shortfall not in (None, "", _PLACEHOLDER, "0"):
        rows.append(_highlight("Connector shortfall", shortfall))
    if unmet not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Unmet reason", unmet))
    if candidate_slots not in (None, "", _PLACEHOLDER, "0"):
        rows.append(_highlight("Candidate slots", candidate_slots))
    platform = capacity.get("platform_upper_bound")
    if platform not in (None, "", _PLACEHOLDER):
        rows.append(_highlight("Platform upper bound", platform))
    if primary == "shape":
        external_lines = capacity.get("external_line_count")
        if external_lines not in (None, "", _PLACEHOLDER):
            rows.append(_highlight("Required normal lines", external_lines))
    return rows


def _layer_outcome(
    *,
    layer_slug: str,
    stack_run_status: str | None,
    completed_layer_slugs: frozenset[str],
    failed_layer_slug: str | None,
    legacy_outcome: str,
) -> str:
    canonical = resolve_canonical_layer_slug(layer_slug)
    completed_canonical = frozenset(resolve_canonical_layer_slug(s) for s in completed_layer_slugs)
    failed_canonical = (
        resolve_canonical_layer_slug(failed_layer_slug) if failed_layer_slug is not None else None
    )
    if failed_canonical == canonical:
        return "failed"
    if layer_slug in completed_layer_slugs or canonical in completed_canonical:
        return "completed"
    if stack_run_status == "timeout_fail_closed":
        return "skipped_budget"
    if stack_run_status is not None:
        if legacy_outcome in {"completed", "failed", "superseded"}:
            return legacy_outcome
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
    completed_layer_slugs = _resolved_completed_layer_slugs(solver_summary)
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
        cli_outcome = _cli_layer_outcome(solver_summary, slug)
        if cli_outcome == "superseded":
            return "superseded"
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
                _highlight("Max throughput / min", headline),
            ],
        ),
        (
            2,
            LAYER_02_EXTERIOR_TRANSPORT,
            "Exterior transport",
            outcome(LAYER_02_EXTERIOR_TRANSPORT, "pending"),
            _layer02_transport_highlights(
                pct=pct,
                target_tp=target_tp,
                l2_required=l2_required,
                l2_planned=l2_planned,
                l2_plan=l2_plan if isinstance(l2_plan, dict) else None,
                capacity=capacity,
                primary=primary,
            ),
        ),
        (
            3,
            (
                LAYER_03_RIM_GREEDY_PLACEMENT
                if _rim_greedy_summary_active(solver_summary)
                else LAYER_03_RIM_MINING_BUNDLES
            ),
            (
                "Rim greedy placement"
                if _rim_greedy_summary_active(solver_summary)
                else "Rim mining bundles"
            ),
            outcome(
                (
                    LAYER_03_RIM_GREEDY_PLACEMENT
                    if _rim_greedy_summary_active(solver_summary)
                    else LAYER_03_RIM_MINING_BUNDLES
                ),
                "pending",
            ),
            (
                _layer03_greedy_highlights(solver_summary)
                if _rim_greedy_summary_active(solver_summary)
                else _layer03_legacy_highlights(
                    solver_summary,
                    target_placement=target_placement,
                    rim_anchor_slots=rim_anchor_slots,
                    route_probed_pool=route_probed_pool,
                    route_probe_succeeded=route_probe_succeeded,
                    capacity_deficit_count=capacity_deficit_count,
                )
            ),
        ),
        (
            4,
            (
                LAYER_04_INNER_PATTERN_FILL
                if _rim_greedy_summary_active(solver_summary)
                else LAYER_04_RIM_BUNDLE_PLACEMENT
            ),
            (
                "Inner pattern fill"
                if _rim_greedy_summary_active(solver_summary)
                else "Rim bundle placement"
            ),
            (
                outcome(LAYER_04_INNER_PATTERN_FILL, "pending")
                if _rim_greedy_summary_active(solver_summary)
                else outcome(LAYER_04_RIM_BUNDLE_PLACEMENT, "pending")
            ),
            (
                _layer04_inner_fill_highlights(solver_summary)
                if _rim_greedy_summary_active(solver_summary)
                else _layer04_rim_bundle_highlights(
                    solver_summary,
                    provisional_placed=provisional_placed,
                    route_probe_succeeded=route_probe_succeeded,
                )
            ),
        ),
        (
            5,
            (
                LAYER_05_TRANSPORT_ROUTING
                if _rim_greedy_summary_active(solver_summary)
                else LAYER_05_INNER_PATTERN_FILL
            ),
            (
                "Transport routing"
                if _rim_greedy_summary_active(solver_summary)
                else "Inner pattern fill"
            ),
            (
                outcome(LAYER_05_TRANSPORT_ROUTING, "pending")
                if _rim_greedy_summary_active(solver_summary)
                else outcome(LAYER_05_INNER_PATTERN_FILL, "pending")
            ),
            (
                _layer04_transport_highlights(solver_summary)
                if _rim_greedy_summary_active(solver_summary)
                else [
                    _highlight("Macro-only mode", solver_summary.get("macro_only_mode")),
                    _highlight(
                        "Macro commits",
                        macro.get("committed_macro_count") if macro else _PLACEHOLDER,
                    ),
                    _highlight(
                        "Macro placements",
                        macro.get("placement_count") if macro else _PLACEHOLDER,
                    ),
                ]
            ),
        ),
        (
            6,
            LAYER_06_COMMIT_VALIDATE,
            "Commit & validate",
            ("failed" if not validation_passed else outcome(LAYER_06_COMMIT_VALIDATE, l5_legacy)),
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
    cards: list[dict[str, Any]] = []
    for index, slug, title, layer_outcome, highlights in layers:
        card_highlights = list(highlights)
        if layer_outcome == "superseded" and not any(
            row.get("value") not in (None, "", _PLACEHOLDER) for row in card_highlights
        ):
            card_highlights = [_highlight("Status", _superseded_status_label(slug))]
        cards.append(
            {
                "layer_index": index,
                "layer_slug": slug,
                "title": title,
                "outcome": layer_outcome,
                "highlights": card_highlights,
            }
        )
    return cards


def lab_run_summary_from_solver_summary(
    *,
    run_id: int,
    status: str,
    solver_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build Evolution Runs / Selected Run Detail payload from persisted summary."""

    solver_summary = solver_summary_for_lab_display(dict(solver_summary))
    issue_codes = list(solver_summary.get("issue_codes") or [])
    issue_details = list(solver_summary.get("issue_details") or [])
    validation_passed = validation_passed_from_solver_summary(solver_summary)
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
    reconstruction = _section_reconstruction(
        solver_summary.get("reconstruction_observability"),
        (
            solver_summary.get("reconstruction_capacity")
            if isinstance(solver_summary.get("reconstruction_capacity"), dict)
            else None
        ),
    )
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


def solver_summary_payload_for_run(run: m.SolverRun) -> dict[str, Any]:
    """Persisted summary for Lab display (artifact column first, legacy config fallback)."""

    cached = dict(run.solver_summary_json or {})
    if cached:
        return cached
    config = dict(run.config_json or {})
    return dict(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY) or {})


def lab_run_summary_from_orm(run: m.SolverRun) -> dict[str, Any]:
    """Serialize one :class:`SolverRun` for Lab template/JSON."""

    summary = solver_summary_payload_for_run(run)
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


def _lab_run_summary_from_row(
    *,
    run_id: int,
    status: str,
    solver_summary: Any,
) -> dict[str, Any]:
    """Serialize one run summary without loading the full ``config_json`` blob."""

    if status == m.SolverRun.RunStatus.COMPLETED:
        ui_status = "completed"
    elif status == m.SolverRun.RunStatus.PARTIAL:
        ui_status = "partial"
    elif status == m.SolverRun.RunStatus.FAILED:
        ui_status = "failed"
    else:
        ui_status = str(status)
    return lab_run_summary_from_solver_summary(
        run_id=int(run_id),
        status=ui_status,
        solver_summary=dict(solver_summary) if isinstance(solver_summary, dict) else {},
    )


def solver_runs_for_lab_project(project_id: int, *, limit: int = 10) -> list[dict[str, Any]]:
    """Latest solver runs for one project (newest first)."""

    rows = (
        m.SolverRun.objects.filter(project_id=int(project_id))
        .order_by("-created_at", "-id")
        .values_list("id", "status", "solver_summary_json")[:limit]
    )
    return [
        _lab_run_summary_from_row(
            run_id=int(run_id),
            status=str(status),
            solver_summary=solver_summary,
        )
        for run_id, status, solver_summary in rows
    ]


__all__ = [
    "lab_run_summary_from_orm",
    "lab_run_summary_from_solver_summary",
    "solver_runs_for_lab_project",
    "solver_summary_for_lab_display",
    "solver_summary_payload_for_run",
    "validation_passed_from_solver_summary",
]
