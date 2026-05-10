"""P4 reclaim: bundle evaluation DTO helpers (gain_ratio ordering)."""

from __future__ import annotations

import math

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    _P4BundleEval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def _p4_bundle_eval(
    *,
    gain: float,
    additional_route_cost: float,
    gain_ratio: float,
    incremental_internal_transport_added: int,
    rejected_reason: str | None,
    accepted_shadow: bool,
    anchor: Coord,
    extension: Coord,
    rotation: int,
    shadow_route_path: tuple[Coord, ...] | None = None,
) -> _P4BundleEval:
    """P4 후보 dict를 정렬 가능한 _P4BundleEval로 변환한다 (§12.2 gain_ratio)."""
    return _P4BundleEval(
        gain=gain,
        additional_route_cost=additional_route_cost,
        gain_ratio=gain_ratio,
        incremental_internal_transport_added=incremental_internal_transport_added,
        rejected_reason=rejected_reason,
        accepted_shadow=accepted_shadow,
        anchor=anchor,
        extension=extension,
        rotation=rotation,
        shadow_route_path=shadow_route_path,
    )


def _p4_accepted_sort_key(e: _P4BundleEval) -> tuple[int | float, ...]:
    """Deterministic ascending sort key: lower is better."""

    if math.isinf(e.gain_ratio):
        gr_key: tuple[int, float] = (0, 0.0)
    else:
        gr_key = (1, -e.gain_ratio)
    return (
        gr_key[0],
        gr_key[1],
        e.additional_route_cost,
        e.anchor[1],
        e.anchor[0],
        e.extension[1],
        e.extension[0],
        e.rotation,
    )


def select_best_accepted_p4_bundle(evals: list[_P4BundleEval]) -> _P4BundleEval | None:
    """accepted P4 후보 중 gain_ratio와 tie-break로 최선 후보를 고른다 (§12.2)."""
    accepted = [e for e in evals if e.accepted_shadow]
    if not accepted:
        return None
    return min(accepted, key=_p4_accepted_sort_key)


def _p4_selected_candidate_rank(evals: list[_P4BundleEval], selected: _P4BundleEval) -> int:
    """선택된 P4 후보가 전체 후보 중 몇 번째인지 계산한다 (§12.2 gain_ratio)."""
    accepted = [e for e in evals if e.accepted_shadow]
    ordered = sorted(accepted, key=_p4_accepted_sort_key)
    for i, e in enumerate(ordered):
        if (
            e.anchor == selected.anchor
            and e.extension == selected.extension
            and e.rotation == selected.rotation
            and math.isclose(e.gain_ratio, selected.gain_ratio)
            and math.isclose(e.additional_route_cost, selected.additional_route_cost)
        ):
            return i
    return 0
