"""Pass1/Pass2 bundle stub→external route probe gate (Stabilization-P1)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_cheap_escape_to_external_detail,
    probe_stub_to_external_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bundle_reject_no_route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as s4_goal,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as finval,
)

Pass2RouteProbeOutcome = Literal["routed", "uncertain"]


def new_pass2_route_probe_stats_sink() -> dict[str, Any]:
    """Default counters merged into Pass12 stats (Pass2 STEP4-aligned probe gate)."""

    return {
        "pass2_probe_goal_set_kind_counts": {"first_route": 0, "subsequent_route": 0},
        "pass2_probe_goal_set_kind": "none",
        "pass2_probe_goal_count": 0,
        "pass2_probe_goal_count_max": 0,
        "pass2_probe_goal_count_sum": 0,
        "pass2_probe_goal_eval_count": 0,
        "pass2_route_uncertain_count": 0,
        "pass2_provisional_unrouted_count": 0,
        "pass2_hard_geometry_reject_count": 0,
        "reachable_component_sample_by_size": {},
    }


@dataclass(frozen=True)
class Pass2RouteProbePack:
    """Context for Pass2 route gate aligned with STEP4 goal-set (merge-aware routing prep)."""

    mineable: frozenset[Coord]
    asteroid: frozenset[Coord]
    cells: dict[Coord, dict[str, Any]]
    existing_layout_analysis: dict[str, Any] | None
    stats_sink: dict[str, Any]


def build_pass2_step4_aligned_routing_goals(
    *,
    transport_kind: str,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None,
    transport_cells_before: frozenset[Coord],
    blocked_for_probe: frozenset[Coord],
) -> tuple[frozenset[Coord], Literal["first_route", "subsequent_route"], int]:
    """Return ``(goal_cells, goal_set_kind, goal_count)`` mirroring STEP4 §3.2."""

    margin = s4_goal.exterior_margin_cells(
        mineable=mineable, asteroid=asteroid, cells=cells, is_external=is_external
    )
    hint_union = s4_goal.trunk_seed_union_from_existing_layout(existing_layout_analysis)
    trunk_seed_by_kind = s4_goal.build_trunk_seed_candidates_by_kind(
        exterior_margin=margin,
        hint_union=hint_union,
        cells=cells,
    )
    existing_reaching = finval.transport_cells_reaching_external(
        set(transport_cells_before), set(blocked_for_probe), is_external
    )
    if existing_reaching:
        goal_set_kind: Literal["first_route", "subsequent_route"] = "subsequent_route"
        committed: dict[str, set[Coord]] = {transport_kind: set(existing_reaching)}
    else:
        goal_set_kind = "first_route"
        committed = {}
    raw_goal = s4_goal.build_step4_goal_set(
        transport_kind,
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=trunk_seed_by_kind,
    )
    return frozenset(raw_goal), goal_set_kind, len(raw_goal)


def _pass2_stats_touch_goal_eval(
    stats_sink: dict[str, Any], *, goal_kind: str, goal_count: int
) -> None:
    counts = stats_sink.setdefault("pass2_probe_goal_set_kind_counts", {})
    counts[goal_kind] = int(counts.get(goal_kind, 0)) + 1
    stats_sink["pass2_probe_goal_eval_count"] = (
        int(stats_sink.get("pass2_probe_goal_eval_count", 0)) + 1
    )
    stats_sink["pass2_probe_goal_count_max"] = max(
        int(stats_sink.get("pass2_probe_goal_count_max", 0)), int(goal_count)
    )
    stats_sink["pass2_probe_goal_count_sum"] = int(
        stats_sink.get("pass2_probe_goal_count_sum", 0)
    ) + int(goal_count)


def _pass2_stats_note_transport_failure(
    stats_sink: dict[str, Any], transport_diag: dict[str, Any]
) -> None:
    tp = transport_diag.get("transport_probe")
    if not isinstance(tp, dict):
        return
    n = tp.get("reachable_cells_in_component")
    if not isinstance(n, int):
        return
    hist = stats_sink.setdefault("reachable_component_sample_by_size", {})
    key = str(n)
    hist[key] = int(hist.get(key, 0)) + 1


def finalize_pass2_route_probe_stats(stats_sink: dict[str, Any]) -> None:
    counts = stats_sink.get("pass2_probe_goal_set_kind_counts")
    total = 0
    if isinstance(counts, dict):
        total = sum(int(v) for v in counts.values() if isinstance(v, int))
    if not isinstance(counts, dict) or total == 0:
        stats_sink["pass2_probe_goal_set_kind"] = "none"
    else:
        dominant = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        stats_sink["pass2_probe_goal_set_kind"] = dominant
    stats_sink["pass2_probe_goal_count"] = int(stats_sink.get("pass2_probe_goal_count_max", 0))


def _pass2_stub_adjacent_baseline_trunk_reaches_external(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord],
) -> tuple[bool, dict[str, Any]]:
    """True when stub 4-neighbors a Pass2-entry baseline trunk cell that reaches external."""

    sx, sy = stub_cell
    for nxt in neighbors4(sx, sy):
        if nxt not in adjacent_preserve_trunk_baseline_cells or nxt not in transport_cells:
            continue
        ok, det = probe_stub_to_external_detail(
            stub_cell=nxt,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
        )
        if ok:
            out = {
                "pass2_preserve_merge_probe": {
                    "via_baseline_trunk_cell": [int(nxt[0]), int(nxt[1])],
                    "stub_cell": [int(sx), int(sy)],
                }
            }
            out.update(det)
            return True, out
    return False, {
        "pass2_preserve_merge_probe": {
            "failure": "no_baseline_adjacent_trunk_path_to_external",
            "stub_cell": [int(sx), int(sy)],
        }
    }


def pass2_bundle_route_probe_decision(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    routing_goal_cells: frozenset[Coord],
    goal_set_kind: str,
    goal_count: int,
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None,
    stats_sink: dict[str, Any] | None,
) -> tuple[Pass2RouteProbeOutcome, dict[str, Any]]:
    """Pass2 gate: ``routed`` when a definite reach exists; else ``uncertain`` (STEP4 decides).

    Uses STEP4-aligned void envelope only (``routing_goal_cells - transport``), not Pass1
    cheap-escape envelopes. ``cheap_escape_probe`` may be ``skipped`` without implying reject.
    """

    if stats_sink is not None:
        _pass2_stats_touch_goal_eval(stats_sink, goal_kind=goal_set_kind, goal_count=goal_count)

    ok_transport, transport_diag = probe_stub_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )
    if ok_transport:
        return "routed", transport_diag

    if stats_sink is not None:
        _pass2_stats_note_transport_failure(stats_sink, transport_diag)

    goal_void_cells = frozenset(
        c for c in routing_goal_cells if c not in transport_cells and c not in blocked_cells
    )
    ok_goal_void, goal_void_diag = probe_stub_cheap_escape_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
        allowed_void_cells=goal_void_cells,
    )
    merged_goal = dict(transport_diag)
    merged_goal["pass2_goal_assisted_probe"] = {
        "allowed_goal_void_cell_count": len(goal_void_cells),
        "success": ok_goal_void,
    }
    merged_goal.update(goal_void_diag)
    if ok_goal_void:
        return "routed", merged_goal

    merge_diag: dict[str, Any]
    if adjacent_preserve_trunk_baseline_cells:
        ok_merge, merge_diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
            stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            adjacent_preserve_trunk_baseline_cells=adjacent_preserve_trunk_baseline_cells,
        )
        merged_goal.update(merge_diag)
        if ok_merge:
            return "routed", merged_goal
    else:
        merge_diag = {
            "pass2_preserve_merge_probe": {
                "skipped": True,
                "reason": "no_pass2_baseline_trunk_context",
            }
        }
        merged_goal.update(merge_diag)

    merged_goal["cheap_escape_probe"] = {
        "skipped": True,
        "reason": "pass2_no_p1_cheap_escape_envelope",
        "note": "skipped_is_not_hard_reject_pass2_defers_to_step4",
    }
    if stats_sink is not None:
        stats_sink["pass2_route_uncertain_count"] = (
            int(stats_sink.get("pass2_route_uncertain_count", 0)) + 1
        )
    return "uncertain", merged_goal


def bundle_route_probe_or_reject(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    trace_location: str,
    bundle_hint: dict[str, Any] | None = None,
    pass1_allow_cheap_escape: bool = False,
    p1_cheap_void_cells: frozenset[Coord] | None = None,
    pass2_adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None = None,
) -> bool:
    """Return True when ``stub_cell`` reaches an external cell; else trace reject and False.

    Used as a **Pass1/Pass2 placement commit safety gate** when Pass2 pack is absent; it does not
    establish STEP4 final merge-aware routes.

    When ``pass1_allow_cheap_escape`` is True (Pass1 only), void tiles inside
    ``p1_cheap_void_cells`` may be used for feasibility; they are **not** committed as transport.
    """

    ok_transport, transport_diag = probe_stub_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )
    if ok_transport:
        return True
    merge_diag: dict[str, Any]
    if pass2_adjacent_preserve_trunk_baseline_cells:
        ok_merge, merge_diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
            stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            adjacent_preserve_trunk_baseline_cells=pass2_adjacent_preserve_trunk_baseline_cells,
        )
        if ok_merge:
            return True
    else:
        merge_diag = {
            "pass2_preserve_merge_probe": {
                "skipped": True,
                "reason": "no_pass2_baseline_trunk_context",
            }
        }
    cheap_diag: dict[str, Any]
    if pass1_allow_cheap_escape and p1_cheap_void_cells is not None:
        ok_cheap, cheap_diag = probe_stub_cheap_escape_to_external_detail(
            stub_cell=stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            allowed_void_cells=p1_cheap_void_cells,
        )
        if ok_cheap:
            return True
    else:
        cheap_diag = {
            "cheap_escape_probe": {
                "skipped": True,
                "reason": "pass2_gate_or_no_void_envelope",
                "pass1_allow_cheap_escape": pass1_allow_cheap_escape,
                "has_void_envelope": p1_cheap_void_cells is not None,
            }
        }
    data = dict(bundle_hint or {})
    data["stub_cell"] = stub_cell
    data["route_probe_context"] = {
        "transport_cell_count": len(transport_cells),
        "blocked_cell_count": len(blocked_cells),
    }
    data.update(transport_diag)
    data.update(merge_diag)
    data.update(cheap_diag)
    trace_bundle_reject_no_route(trace_location, data)
    return False
