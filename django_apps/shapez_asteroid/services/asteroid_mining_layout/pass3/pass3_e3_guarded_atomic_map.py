"""P3-E3 guarded atomic candidate map merge (pure, no layout mutation)."""

from __future__ import annotations

import math

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
)


def _p3e3_route_length_ratio_allowed(
    *,
    baseline_route_length: int | None,
    candidate_route_length: int | None,
    max_route_length_ratio: float = MAX_ROUTE_LENGTH_RATIO,
) -> bool:
    """STEP 5 Pass3 reroute bound: ``candidate <= ceil(baseline * max_route_length_ratio)``."""

    if baseline_route_length is None or candidate_route_length is None:
        return False
    allowed = math.ceil(float(baseline_route_length) * float(max_route_length_ratio))
    return candidate_route_length <= allowed


def _p3e3_build_atomic_candidate_map(
    *,
    current_transport_cells: frozenset[Coord],
    cells_to_remove: frozenset[Coord],
    replacement_route_cells: frozenset[Coord],
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    soft_protected_corridors: frozenset[Coord],
    baseline_route_length: int | None,
    candidate_route_length: int | None,
    attempted: bool = True,
) -> P3E3GuardedCommitCandidate:
    """Pure merge + early rejection rules (no layout mutation)."""

    ratio: float | None = None
    baseline_len = baseline_route_length
    candidate_len = candidate_route_length
    if baseline_len is not None and baseline_len != 0 and candidate_len is not None:
        ratio = float(candidate_len) / float(baseline_len)

    touched_hard = frozenset(cells_to_remove & hard_protected_corridors)
    touched_soft = frozenset(cells_to_remove & soft_protected_corridors)

    rr = (
        P3E3_REJECT_FIXED_STUB_REMOVAL
        if cells_to_remove & fixed_output_stubs
        else (
            P3E3_REJECT_HARD_PROTECTED_CORRIDOR
            if touched_hard
            else (
                P3E3_REJECT_NO_REPLACEMENT_ROUTE
                if (cells_to_remove & soft_protected_corridors and not replacement_route_cells)
                else None
            )
        )
    )

    if rr is not None:
        return P3E3GuardedCommitCandidate(
            attempted=attempted,
            candidate_transport_cells=frozenset(),
            removed_transport_cells=cells_to_remove,
            added_transport_cells=frozenset(),
            preserved_stub_cells=fixed_output_stubs,
            touched_hard_protected_cells=touched_hard,
            touched_soft_protected_cells=touched_soft,
            replacement_route_cells=replacement_route_cells,
            baseline_route_length=baseline_route_length,
            candidate_route_length=candidate_route_length,
            route_length_ratio=ratio,
            precheck_passed=False,
            rejected_reason=rr,
            hard_protected_corridors=hard_protected_corridors,
        )

    candidate_transport_cells = (
        current_transport_cells - cells_to_remove | replacement_route_cells | fixed_output_stubs
    )
    added_transport_cells = frozenset(candidate_transport_cells - current_transport_cells)
    return P3E3GuardedCommitCandidate(
        attempted=attempted,
        candidate_transport_cells=candidate_transport_cells,
        removed_transport_cells=cells_to_remove,
        added_transport_cells=added_transport_cells,
        preserved_stub_cells=fixed_output_stubs,
        touched_hard_protected_cells=touched_hard,
        touched_soft_protected_cells=touched_soft,
        replacement_route_cells=replacement_route_cells,
        baseline_route_length=baseline_route_length,
        candidate_route_length=candidate_route_length,
        route_length_ratio=ratio,
        precheck_passed=True,
        rejected_reason=None,
        hard_protected_corridors=hard_protected_corridors,
    )
