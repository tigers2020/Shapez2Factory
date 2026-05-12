"""Timeline helpers: layout counts, post-reclaim Pass3 run-once, internal transport tallies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    post_reclaim_p3e3_route_ratio_max,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
    count_internal_transport_tiles_for_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs,
    layout_kind,
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    validate_final_mining_layout,
)

_EXTRACTORS = EXTRACTORS_SHAPE | EXTRACTORS_FLUID
_EXTENSIONS = EXTENSIONS


def count_internal_transport_tiles_for_kind(
    cells: dict[Coord, dict[str, Any]],
    *,
    transport_kind: str,
    is_external: Callable[[Coord], bool],
) -> int:
    """Count ``want_role(transport_kind)`` tiles not marked external (Pass3 metric)."""

    wr = want_role(transport_kind)
    return count_internal_transport_tiles_for_role(cells, want_role=wr, is_external=is_external)


def _internal_transport_count_for_pass3_kind(
    mining_map: list[dict[str, Any]],
    *,
    is_external: Callable[[Coord], bool],
) -> int | None:
    """Count interior transport tiles for Pass3's single ``transport_kind`` (belt or pipe).

    Mirrors the head of ``run_pass3_transport_minimization_from_maps``: ``None`` when there
    are no routing jobs or mixed transport kinds (Pass3 would skip).
    """

    raw = cells_dict_from_mining_map(mining_map)
    cells = {k: dict(v) for k, v in raw.items()}
    jobs = collect_routing_jobs(cells)
    if not jobs:
        return None
    if len({j[2] for j in jobs}) != 1:
        return None
    tk = jobs[0][2]
    return count_internal_transport_tiles_for_kind(
        cells, transport_kind=tk, is_external=is_external
    )


def optimization_baseline_internal_transport_pre_step4(
    map_after_pass2: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
) -> int | None:
    """Pass1·Pass2 확정 직후(STEP4 이전) 스냅샷의 내부 transport baseline 카운트.

    Pass3 ``before_internal_transport_count``와 동일 계약: 단일 ``transport_kind`` 라우팅
    job이 있을 때만 정수를 반환하고, job 없음·혼합 transport면 ``None``. 내부 타일은
    ``not is_external(c)`` 인 동종 belt/pipe 셀 수(``final_mining_map`` 인자는 API 호환용으로
    유지되며 내부 카운트에는 사용하지 않음).
    """

    _ = final_mining_map
    return _internal_transport_count_for_pass3_kind(map_after_pass2, is_external=is_external)


def _attach_post_reclaim_pass3_count_aliases(out: dict[str, Any]) -> None:
    """Stable short names on top of ``post_reclaim_pass3_before_internal_transport_count`` etc."""

    bi = out.get("post_reclaim_pass3_before_internal_transport_count")
    ai = out.get("post_reclaim_pass3_after_internal_transport_count")
    if bi is not None:
        out["post_reclaim_pass3_before_count"] = int(bi)
    if ai is not None:
        out["post_reclaim_pass3_after_count"] = int(ai)
    if bi is not None and ai is not None:
        out["post_reclaim_pass3_delta"] = int(bi) - int(ai)


def _run_post_reclaim_pass3_once(
    mining_map: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    pass3_summary: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One Pass3 pass on ``mining_map``; emit ``post_reclaim_pass3_*`` summary fields."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_service as _solver,
    )

    ps = pass3_summary or {}
    pr_cap = post_reclaim_p3e3_route_ratio_max(
        pass3_internal_transport_saved=int(ps.get("pass3_internal_transport_saved") or 0),
    )
    map_try, _p3_res, p3_trace = _solver.run_pass3_transport_minimization_from_maps(
        mining_map,
        final_mining_map=final_mining_map,
        is_external=is_external,
        routing_state_summary=None,
        p3e3_atomic_route_ratio_max=pr_cap,
    )
    out: dict[str, Any] = {
        "post_reclaim_pass3_reruns_used": 1,
        "post_reclaim_pass3_attempted": True,
        "post_reclaim_pass3_ran": True,
    }
    for k, v in p3_trace.items():
        if (
            k.startswith("p3e2_")
            or k.startswith("p3e3_")
            or k in ("pass3_greedy_committed", "pass3_greedy_local_replacement")
        ):
            out[f"post_reclaim_pass3_{k}"] = v
            if k == "pass3_greedy_local_replacement":
                # Shorter alias (avoids ``post_reclaim_pass3_pass3_*`` duplication); keep long key.
                out["post_reclaim_pass3_greedy_local_replacement"] = v
    metric_keys = (
        "before_transport_count",
        "after_transport_count",
        "pass3_transport_cells_removed_total",
        "pass3_internal_transport_saved",
        "before_internal_transport_count",
        "after_internal_transport_count",
        "gain",
        "pass3_committed",
    )
    for kk in metric_keys:
        if kk in p3_trace:
            out[f"post_reclaim_pass3_{kk}"] = p3_trace[kk]
    if "pass3_connectivity_reject_sample" in p3_trace:
        out["post_reclaim_pass3_pass3_connectivity_reject_sample"] = p3_trace[
            "pass3_connectivity_reject_sample"
        ]
    _attach_post_reclaim_pass3_count_aliases(out)

    if p3_trace.get("pass3_skipped"):
        out["post_reclaim_pass3_executed"] = False
        out["post_reclaim_pass3_map_accepted"] = False
        out["post_reclaim_pass3_skip_reason"] = str(
            p3_trace.get("pass3_skip_reason") or "pass3_skipped"
        )
        return mining_map, out

    report_try = validate_final_mining_layout(map_try)
    if report_try.geometry_valid and report_try.connectivity_valid:
        out["post_reclaim_pass3_executed"] = True
        out["post_reclaim_pass3_map_accepted"] = True
        out["post_reclaim_pass3_skip_reason"] = None
        if p3_trace.get("pass3_committed"):
            if "commit_reason" in p3_trace:
                out["post_reclaim_pass3_pass3_commit_reason"] = p3_trace["commit_reason"]
        else:
            rr = p3_trace.get("rejected_reason")
            if rr is not None:
                out["post_reclaim_pass3_pass3_rejected_reason"] = rr
        return map_try, out

    out["post_reclaim_pass3_executed"] = False
    out["post_reclaim_pass3_map_accepted"] = False
    out["post_reclaim_pass3_skip_reason"] = "final_validation_failed_after_post_reclaim_pass3"
    out["post_reclaim_pass3_pass3_reverted"] = True
    return mining_map, out


def count_layout_cells(mining_map: list[dict[str, Any]]) -> dict[str, int]:
    """Count extractors, extensions, and belt/pipe transport tiles."""

    ex = ext = tr = 0
    for row in mining_map:
        lk = layout_kind(row)
        role = row.get("role")
        if role == "belt" or role == "pipe":
            tr += 1
        elif lk in _EXTRACTORS:
            ex += 1
        elif lk in _EXTENSIONS:
            ext += 1
    return {"extractors": ex, "extensions": ext, "transport_cells": tr}


def _pre_pass12_reference_counts(map_timeline: list[dict[str, Any]]) -> dict[str, int]:
    """Counts before Pass1/Pass2: shell bodies (timeline index 1) plus ``with_transport`` belts."""

    shell = map_timeline[1]["mining_map"]
    transport = map_timeline[0]["mining_map"]
    bodies = count_layout_cells(shell)
    bodies["transport_cells"] = count_layout_cells(transport)["transport_cells"]
    return bodies


def _solver_stats_by_prefix(stats: dict[str, Any], prefix: str) -> dict[str, Any]:
    """solver summary에서 특정 prefix metric만 추출한다 (§4 pipeline control flow)."""
    return {k: v for k, v in stats.items() if k.startswith(prefix)}


def _placement_candidate_blocked_count_from_pass12(pass12_stats: Mapping[str, Any] | None) -> int:
    """Pass12 ``placement_candidate_blocked_count`` for summary / replay metrics (default 0)."""

    if pass12_stats is None:
        return 0
    v = pass12_stats.get("placement_candidate_blocked_count")
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    return 0
