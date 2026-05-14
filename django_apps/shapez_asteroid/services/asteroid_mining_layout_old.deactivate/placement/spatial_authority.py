"""Spatial authority: canonical layout representations per solver phase (desync guard).

``mining_map`` row lists are the persisted truth after each merge/commit frame.
``Pass12LayoutScratch`` sets are authoritative only *during* Pass1/Pass2 in-flight placement,
before rows are materialized. STEP4 mutates a cell dict derived from ``mining_map``; P4 reclaim
mutates ``mining_map`` rows via ``SolverMutationTransaction``. ``routing_state`` protected
pools are derived from committed STEP4 routes, not independent sources of belt geometry.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)


def authority_note_for_phase(phase: str) -> str:
    """Short note: which representation callers should treat as canonical for ``phase``."""

    table: dict[str, str] = {
        "pass12_inflight": (
            "Pass12LayoutScratch.transport_cells/blocked_cells + placement_records; "
            "mining_map rows updated only after _merge_pass1_into_rows."
        ),
        "post_pass12_merge": "mining_map row list (pass2 merged).",
        "step4_inflight": (
            "Internal cells dict in step4_merge_routing (copy of map); output rows replace map."
        ),
        "post_step4": "mining_map after STEP4 (ROUTED_CONFIRMED / ROLLED_BACK row metadata).",
        "pass3": "mining_map rows after transport minimization commits.",
        "p4_reclaim": "mining_map via SolverMutationTransaction.working_map; baseline on rollback.",
        "protected_corridors": (
            "routing_state hard/soft pools are policy overlays derived from committed STEP4 "
            "routes — not a second transport graph."
        ),
    }
    return table.get(phase, "See module docstring; phase unknown.")


def transport_coords_from_mining_map(
    mining_map: list[dict[str, Any]],
    *,
    transport_kind: str,
) -> set[Coord]:
    """Read-only: belt/pipe coordinates for ``transport_kind`` (shape_belt vs fluid_pipe)."""

    wr = want_role(transport_kind)
    out: set[Coord] = set()
    for row in mining_map:
        if row.get("role") == wr:
            x, y = row.get("x"), row.get("y")
            if isinstance(x, int) and isinstance(y, int) and x != 0:
                out.add((x, y))
    return out


def infer_transport_kind_from_mining_map(mining_map: list[dict[str, Any]]) -> str:
    """First belt/pipe row wins; default ``shape_belt`` when no transport (STEP9 helper)."""

    for row in mining_map:
        role = row.get("role")
        if role == "pipe":
            return "fluid_pipe"
        if role == "belt":
            return "shape_belt"
    return "shape_belt"


def _coords_from_corridor_list(raw: Any) -> list[Coord]:
    out: list[Coord] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if (
            isinstance(item, (list, tuple))
            and len(item) >= 2
            and isinstance(item[0], int)
            and isinstance(item[1], int)
            and item[0] != 0
        ):
            out.append((item[0], item[1]))
    return out


def assert_protected_corridors_agree_with_transport_map(
    routing_state: dict[str, Any] | None,
    mining_map: list[dict[str, Any]],
    *,
    transport_kind: str,
    context: str = "",
) -> None:
    """STEP9 guard: STEP4 hard/soft protected coords are ``want_role`` cells on ``mining_map``."""

    if not routing_state:
        return
    wr = want_role(transport_kind)
    cells = cells_dict_from_mining_map(mining_map)
    coords: list[Coord] = []
    for key in ("hard_protected_corridors", "soft_protected_corridors"):
        coords.extend(_coords_from_corridor_list(routing_state.get(key)))
    missing: list[Coord] = []
    for c in coords:
        row = cells.get(c)
        if row is None or row.get("role") != wr:
            missing.append(c)
    if missing:
        msg = f"protected corridor not on map as {wr} ({context}): {missing[:8]}"
        if len(missing) > 8:
            msg += f"... (+{len(missing) - 8} more)"
        raise ValueError(msg)


def assert_scratch_transport_subset_of_map(
    scratch: Pass12LayoutScratch,
    mining_map: list[dict[str, Any]],
    *,
    context: str = "",
    materialized_scratch_transport: frozenset[Coord] | None = None,
) -> None:
    """Debug guard: materialized scratch transport cells must appear as belt/pipe on ``mining_map``.

    When ``materialized_scratch_transport`` is set (Pass12 narrow restamp), only those coords are
    checked; unstamped orphan scratch coords are ignored.
    """

    wr = want_role(scratch.transport_kind)
    cells = cells_dict_from_mining_map(mining_map)
    to_check = materialized_scratch_transport
    if to_check is None:
        to_check = frozenset(c for c in scratch.transport_cells if c not in scratch.blocked_cells)
    missing: list[Coord] = []
    for c in to_check:
        row = cells.get(c)
        if row is None or row.get("role") != wr:
            missing.append(c)
    if missing:
        msg = f"scratch transport not on map ({context}): {missing[:8]}"
        if len(missing) > 8:
            msg += f"... (+{len(missing) - 8} more)"
        raise ValueError(msg)
