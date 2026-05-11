"""Pass1/Pass2 bundle stub→external route probe gate (Stabilization-P1)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_cheap_escape_to_external_detail,
    probe_stub_to_external_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bundle_reject_no_route,
)


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

    Used as a **Pass1/Pass2 placement commit safety gate**; it does not establish
    STEP4 final merge-aware routes.

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
