"""Solver 요약의 크기 변화량 분배 헬퍼."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _internal_transport_count_for_pass3_kind,
    count_layout_cells,
)


def removed_counts_distribution(
    *,
    before_counts: dict[str, int],
    after_counts: dict[str, int],
) -> dict[str, int]:
    """Pass1/Pass2 전후 감소량을 공개 summary 필드에 맞춰 분배한다."""

    return {
        "extractors": _positive_delta(before_counts, after_counts, "extractors"),
        "extensions": _positive_delta(before_counts, after_counts, "extensions"),
        "transport_cells": _positive_delta(before_counts, after_counts, "transport_cells"),
    }


def attach_pass3_size_distribution(
    pass3_summary: dict[str, Any],
    *,
    map_final: list[dict[str, Any]],
) -> None:
    """Pass3 전후 크기 변화량을 summary에 채운다."""

    after_counts = count_layout_cells(map_final)
    pass3_summary["after_pass3_counts"] = dict(after_counts)
    before_counts = pass3_summary.get("before_pass3_counts")
    if isinstance(before_counts, dict):
        pass3_summary["pass3_transport_cells_removed"] = max(
            0,
            int(before_counts.get("transport_cells", 0))
            - int(after_counts.get("transport_cells", 0)),
        )


def attach_net_internal_transport_saved_after_reclaim(
    pass3_summary: dict[str, Any],
    *,
    map_final: list[dict[str, Any]],
    final_mining_map: list[dict[str, Any]],
) -> None:
    """P4 reclaim 이후 내부 transport 절감량을 summary에 채운다."""

    baseline_entry = pass3_summary.get("baseline_internal_transport_at_reclaim_entry")
    if not isinstance(baseline_entry, int):
        return
    final_internal_transport = _internal_transport_count_for_pass3_kind(
        map_final,
        final_mining_map=final_mining_map,
    )
    if isinstance(final_internal_transport, int):
        pass3_summary["net_internal_transport_saved_after_reclaim"] = int(baseline_entry) - int(
            final_internal_transport
        )


def _positive_delta(
    before_counts: dict[str, int],
    after_counts: dict[str, int],
    key: str,
) -> int:
    """음수 변화량은 제거량으로 세지 않는다."""

    return max(0, int(before_counts.get(key, 0)) - int(after_counts.get(key, 0)))
